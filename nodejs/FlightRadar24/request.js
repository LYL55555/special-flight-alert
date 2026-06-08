const {CloudflareError} = require("./errors");
const {Session, ClientIdentifier, initTLS} = require("node-tls-client");

const FormData = require("form-data");
const fetch = (...args) => import("node-fetch").then(({default: fetch}) => fetch(...args));

let tlsInitPromise = null;
let tlsSession = null;

/**
 * Return a shared TLS session that impersonates Chrome.
 *
 * @return {Promise<Session>}
 */
async function getTlsSession() {
    if (!tlsInitPromise) {
        tlsInitPromise = initTLS();
    }
    await tlsInitPromise;

    if (!tlsSession) {
        tlsSession = new Session({clientIdentifier: ClientIdentifier.chrome_131});
    }
    return tlsSession;
}

/**
 * Return whether the request should keep node-fetch for binary image payloads.
 *
 * @param {object|null} headers
 * @return {boolean}
 */
function needsBinaryFetch(headers) {
    const accept = (headers?.accept || headers?.Accept || "").toLowerCase();
    const primaryType = accept.split(",")[0].trim();
    return primaryType.startsWith("image/");
}

/**
 * Wrap a node-tls-client response in a fetch-compatible object.
 *
 * @param {object} tlsResponse
 * @return {object}
 */
function wrapTlsResponse(tlsResponse) {
    const headerMap = {};

    for (const [key, value] of Object.entries(tlsResponse.headers || {})) {
        headerMap[key.toLowerCase()] = Array.isArray(value) ? value.join(", ") : value;
    }

    const body = tlsResponse.body || "";

    return {
        status: tlsResponse.status,
        statusText: tlsResponse.status >= 200 && tlsResponse.status < 300 ? "OK" : "Forbidden",
        headers: {
            forEach(callback) {
                for (const [key, value] of Object.entries(headerMap)) {
                    callback(value, key);
                }
            },
            raw() {
                const raw = {};

                if (tlsResponse.cookies) {
                    raw["set-cookie"] = Object.entries(tlsResponse.cookies).map(
                        ([key, value]) => `${key}=${value}`,
                    );
                }

                return raw;
            },
        },
        async json() {
            return JSON.parse(body);
        },
        async text() {
            return body;
        },
        async arrayBuffer() {
            const buffer = Buffer.from(body, "utf8");
            return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
        },
    };
}

/**
 * Class to make requests to the FlightRadar24.
 */
class APIRequest {
    /**
     * Constructor of the APIRequest class.
     *
     * @param {string} [url]
     * @param {object} [params]
     * @param {object} [headers]
     * @param {object} [data]
     * @param {object} [cookies]
     * @param {object} [excludeStatusCodes=[]]
     */
    constructor(url, params = null, headers = null, data = null, cookies = null, excludeStatusCodes = []) {
        this.requestParams = {
            "params": params,
            "headers": headers,
            "data": data,
            "cookies": cookies,
        };

        this.requestMethod = data == null ? "GET" : "POST";
        this.__excludeStatusCodes = excludeStatusCodes;

        if (params != null && Object.keys(params).length > 0) {
            url += "?";

            for (const key in params) {
                if (Object.prototype.hasOwnProperty.call(params, key)) { // guard-for-in
                    url += key + "=" + params[key] + "&";
                }
            }
            url = url.slice(0, -1);
        }

        this.url = url;

        this.__response = {};
        this.__content = null;
    }

    /**
     * Send the request and receive a response.
     *
     * @return {this}
     */
    async receive() {
        const headers = {...(this.requestParams["headers"] || {})};
        const cookies = this.requestParams["cookies"];

        if (this.requestMethod === "POST") {
            const formData = new FormData();

            Object.entries(this.requestParams["data"]).forEach(([key, value]) => {
                formData.append(key, value);
            });

            if (needsBinaryFetch(headers)) {
                const settings = {
                    method: "POST",
                    headers: {...headers, ...formData.getHeaders()},
                    body: formData,
                    cookies: cookies,
                };
                this.__response = await fetch(this.url, settings);
            }
            else {
                const session = await getTlsSession();
                const tlsResponse = await session.post(this.url, {
                    headers: {...headers, ...formData.getHeaders()},
                    body: formData.getBuffer(),
                    cookies: cookies,
                });
                this.__response = wrapTlsResponse(tlsResponse);
            }
        }
        else if (needsBinaryFetch(headers)) {
            this.__response = await fetch(this.url, {
                method: "GET",
                headers: headers,
                cookies: cookies,
            });
        }
        else {
            const session = await getTlsSession();
            const tlsResponse = await session.get(this.url, {
                headers: headers,
                cookies: cookies,
            });
            this.__response = wrapTlsResponse(tlsResponse);
        }

        if (this.getStatusCode() == 520) {
            throw new CloudflareError(
                "An unexpected error has occurred. Perhaps you are making too many calls?",
                this.__response,
            );
        }

        if (!this.__excludeStatusCodes.includes(this.getStatusCode())) {
            if (![200, 201, 202].includes(this.getStatusCode())) {
                throw new Error(
                    "Received status code '" +
                    this.getStatusCode() + ": " +
                    this.__response.statusText + "' for the URL " +
                    this.url,
                );
            }
        }
        return this;
    }

    /**
     * Return the received content from the request.
     */
    async getContent() {
        if (this.__content !== null) {
            return this.__content;
        }

        let contentType = this.getHeaders()["content-type"];
        contentType = contentType == null ? "" : contentType;

        if (contentType.includes("application/json")) {
            this.__content = await this.__response.json();
        }
        else if (contentType.includes("text")) {
            this.__content = await this.__response.text();
        }
        else {
            this.__content = await this.__response.arrayBuffer();
        }
        return this.__content;
    }

    /**
     * Return the received cookies from the request.
     */
    getCookies() {
        const rawCookies = this.__response.headers.raw()["set-cookie"];
        const cookies = {};

        if (rawCookies == null) {
            return {};
        }

        rawCookies.forEach((string) => {
            const keyAndValue = string.split(";")[0].split("=");
            cookies[keyAndValue[0]] = keyAndValue[1];
        });

        return cookies;
    }

    /**
     * Return the headers of the response.
     */
    getHeaders() {
        const headersAsDict = {};

        this.__response.headers.forEach((value, key) => {
            headersAsDict[key] = value;
        });
        return headersAsDict;
    }

    /**
     * Return the received response object.
     */
    getResponseObject() {
        return this.__response;
    }

    /**
     * Return the status code of the response.
     */
    getStatusCode() {
        return this.__response.status;
    }
}

module.exports = APIRequest;
