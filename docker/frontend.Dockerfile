FROM nginx:alpine

# Copy the frontend files to the nginx html directory
COPY frontend/ /usr/share/nginx/html/

# Copy the custom nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
