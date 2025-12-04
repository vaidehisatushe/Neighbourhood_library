FROM node:18-alpine
WORKDIR /app
COPY gateway/package.json ./
RUN npm install --production
COPY gateway/ .
COPY protos/ ../protos/
EXPOSE 8080
CMD ["node", "server.js"]
