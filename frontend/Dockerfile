FROM node:20-alpine

WORKDIR /app

# Copy package configurations and install node modules
COPY package.json package-lock.json* ./
RUN npm install

# Copy complete UI source tree
COPY . .

EXPOSE 5173

# Bind Vite local dev server to all network interfaces for container exposure
CMD ["npm", "run", "dev", "--", "--host"]
