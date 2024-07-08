# ���������� ����������� ����� Python
FROM python:3.10

# ������������� ������� ����������
WORKDIR /app

# ���������� ���������
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ��������� pip
RUN pip install --upgrade pip

# �������� ���� ������������
COPY requirements.txt /app/

# ������������� �����������
RUN pip install --no-cache-dir -r requirements.txt

# �������� �������� ��� �������
COPY .env /app/.env

# ������� ��� ���������� �������� � ������� ����������� ������� ���������� Django
CMD ["sh", "-c", "python swim_graph/manage.py migrate && python swim_graph/manage.py runserver 0.0.0.0:8000"]
