# Sử dụng Python nhẹ nhất
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào image
COPY . .

# Expose port 80
EXPOSE 80

# Chạy app bằng Gunicorn (Production server) thay vì Flask dev server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]

