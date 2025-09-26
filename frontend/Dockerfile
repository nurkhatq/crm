FROM node:18-alpine

WORKDIR /app

# Set memory limits for Node.js
ENV NODE_OPTIONS="--max-old-space-size=512"

# Copy package files
COPY package*.json ./

# Install dependencies with memory optimization
RUN npm ci --only=production --no-audit --no-fund

# Create non-root user first
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy source code
COPY --chown=nextjs:nodejs . .

# Create .next directory with proper permissions
RUN mkdir -p /app/.next && chown -R nextjs:nodejs /app/.next

USER nextjs

# Expose port
EXPOSE 3000

# Start development server with memory optimization
CMD ["npm", "run", "dev"]
