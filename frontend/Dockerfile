# syntax=docker/dockerfile:1

FROM node:24.11.1-alpine AS builder
ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.30-alpine

ENV PORT=8080

RUN apk upgrade --no-cache

RUN rm -f /etc/nginx/conf.d/*.conf \
 && printf '%s\n' \
    'server {' \
    '    listen 8080;' \
    '    listen [::]:8080;' \
    '    server_name _;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    client_body_temp_path /tmp/nginx-cache/client_body;' \
    '    proxy_temp_path /tmp/nginx-cache/proxy;' \
    '    fastcgi_temp_path /tmp/nginx-cache/fastcgi;' \
    '    uwsgi_temp_path /tmp/nginx-cache/uwsgi;' \
    '    scgi_temp_path /tmp/nginx-cache/scgi;' \
    '    location = /healthz {' \
    '        access_log off;' \
    '        default_type text/plain;' \
    '        return 200 "ok";' \
    '    }' \
    '    location /assets/ {' \
    '        expires 1y;' \
    '        add_header Cache-Control "public, immutable";' \
    '        try_files $uri =404;' \
    '    }' \
    '    location / {' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

RUN sed -i 's@^pid .*@pid /tmp/nginx.pid;@' /etc/nginx/nginx.conf \
 && sed -i '/^user /d' /etc/nginx/nginx.conf \
 && mkdir -p /tmp/nginx-cache \
 && chown -R nginx:nginx /tmp/nginx-cache /usr/share/nginx/html /var/cache/nginx

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
