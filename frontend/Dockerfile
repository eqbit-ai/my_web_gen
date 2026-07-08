# ─────────────────────────────────────────────────────────────
# Stage 1: Build React App
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Accept build argument from Railway
ARG REACT_APP_API_URL

# Make it available during React build
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Debug (remove later)
RUN echo "================================="
RUN echo "REACT_APP_API_URL=${REACT_APP_API_URL}"
RUN echo "================================="

# Build React application
RUN npm run build

# ─────────────────────────────────────────────────────────────
# Stage 2: Nginx
# ─────────────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy React build
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]