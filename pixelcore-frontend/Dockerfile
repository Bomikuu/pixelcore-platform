# Use the latest LTS Node.js image
FROM node:lts

# Set working directory
WORKDIR /app

# Install dependencies inside the image. The source directory is bind-mounted
# in development, so node_modules must not come from the host OS.
COPY package*.json ./
RUN npm ci

COPY . .

# Expose the Nuxt development server port
EXPOSE 3000

# Start the Nuxt application in development mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
