# synapse-admin is a fully static SPA; upstream publishes a prebuilt dist
# tarball (built with a relative base path) per release, so we serve that
# directly instead of building from source.
ARG SYNAPSE_ADMIN_VERSION=0.11.4

FROM alpine:3.21 AS fetch
ARG SYNAPSE_ADMIN_VERSION
ARG SYNAPSE_ADMIN_SHA256=fe76fc198540b6ecd29cca0f689e61c6de1183f9d2a4b6662734c2e69cbcb2c9

RUN wget -q -O /tmp/synapse-admin.tar.gz \
      "https://github.com/Awesome-Technologies/synapse-admin/releases/download/${SYNAPSE_ADMIN_VERSION}/synapse-admin-${SYNAPSE_ADMIN_VERSION}.tar.gz" \
 && echo "${SYNAPSE_ADMIN_SHA256}  /tmp/synapse-admin.tar.gz" | sha256sum -c - \
 && mkdir /app \
 && tar xzf /tmp/synapse-admin.tar.gz --strip-components=1 -C /app \
 # upstream releases ship index.html with this vite placeholder unsubstituted,
 # which throws in the browser and leaves the footer version blank
 && sed -i "s/__SYNAPSE_ADMIN_VERSION__/\"${SYNAPSE_ADMIN_VERSION}\"/" /app/index.html

FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=fetch /app /usr/share/nginx/html

EXPOSE 8080
