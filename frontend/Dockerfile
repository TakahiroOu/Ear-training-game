# Development image for the React frontend.
# Start from an official image that already has Node.js installed.
FROM node:22-alpine

WORKDIR /app

# Install libraries first (copying only package files lets Docker reuse this step
# when you change your code but not your dependencies).
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the code.
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
