# Quy tắc code: Lint và Format



## Backend — Python



Sử dụng [Ruff](https://docs.astral.sh/ruff/) để kiểm tra lỗi và định dạng code Python.



Chạy tại thư mục gốc dự án:



```powershell

# Kiểm tra lint

python -m ruff check backend



# Tự động sửa các lỗi lint có thể sửa

python -m ruff check backend --fix



# Định dạng code

python -m ruff format backend



# Kiểm tra code đã đúng định dạng

python -m ruff format --check backend

```



Cài đặt các dependency backend bằng:



```powershell

python -m pip install -r backend/requirements.txt

```



## Frontend — React



Sử dụng ESLint để kiểm tra code và Prettier để định dạng code.



Chạy tại thư mục `frontend`:



```powershell

# Cài đặt dependency

npm install



# Kiểm tra lint

npm run lint



# Định dạng code

npm run format



# Kiểm tra định dạng mà không sửa file

npm run format:check

```



## Tiêu chí hoàn thành



- `python -m ruff check backend` không có lỗi.

- `python -m ruff format --check backend` xác nhận các file đã được định dạng.

- `npm run lint` không có lỗi.

- `npm run format:check` xác nhận các file frontend đã đúng định dạng.



