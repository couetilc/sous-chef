# syntax=docker/dockerfile:1.7-labs

FROM node:24.9.0-bookworm-slim
# FROM node:24.9.0-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./

RUN corepack enable

RUN pnpm install

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
