# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the SvelteKit app (outputs to build/ with adapter-node)
RUN npm run build

# List contents to verify build output
RUN ls -la && ls -la build/ || echo "Build directory not found"

# Production stage
FROM node:20-slim

WORKDIR /app

# Copy the entire build output from adapter-node
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json

# Install only production dependencies
RUN npm ci --only=production

# Expose port (Railway sets PORT env variable dynamically)
EXPOSE 3000

# Start the app (adapter-node respects PORT env var automatically)
CMD ["node", "build/index.js"]
