FROM node:22-bookworm-slim

WORKDIR /app

COPY web/package.json ./
RUN npm install --omit=dev

COPY web/ ./
COPY questions.json /questions.json

ENV NODE_ENV=production \
    WEB_PORT=3000 \
    BOT_API_BASE=http://bot-api:5050 \
    QUESTIONS_PATH=/questions.json \
    DB_HOST=mysql \
    DB_PORT=3306 \
    DB_USER=aac \
    DB_PASSWORD=aacpass \
    DB_NAME=answer_and_conquer

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "app.js"]
