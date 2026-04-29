# Stage 1 — build
FROM node:22-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# VITE_API_URL is baked into the bundle at build time
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

# Stage 2 — serve
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
