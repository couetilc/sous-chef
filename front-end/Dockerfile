# syntax=docker/dockerfile:1.7-labs

FROM node:24.9.0-bookworm-slim as builder
# FROM node:24.9.0-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./

RUN corepack enable

RUN pnpm install

COPY . .

EXPOSE 5173

FROM builder as dev

COPY --from=builder /app /app

CMD ["pnpm", "dev", "--host", "0.0.0.0"]

FROM builder as prod

COPY --from=builder /app /app

RUN ["pnpm", "build"]
