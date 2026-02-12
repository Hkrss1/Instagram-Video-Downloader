# Load Balancer Readiness Notes

This app includes:
- `ProxyFix` for forwarded headers (`X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`)
- Health endpoint: `/api/health`
- Readiness endpoint: `/api/ready`

## Example Nginx Upstream (VPS)

```nginx
upstream video_downloader_app {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://video_downloader_app;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    location /health {
        proxy_pass http://video_downloader_app/api/health;
    }

    location /ready {
        proxy_pass http://video_downloader_app/api/ready;
    }
}
```

## Notes

- cPanel shared hosting typically does not let you configure upstream load balancing.
- For true load balancing, deploy on VPS/Cloud and use Nginx/HAProxy/Cloud LB.
