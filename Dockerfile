FROM nginx:alpine

# Create app directory
WORKDIR /usr/share/nginx/html

# Copy static files
COPY index.html .
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Create empty config.js file
RUN touch /usr/share/nginx/html/config.js

# Make entrypoint script executable
RUN chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
