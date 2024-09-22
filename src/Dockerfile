FROM python:3.11.1-buster as builder

ENV TZ=Asia/Yekaterinburg
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS="ignore:Unverified HTTPS request"

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache \
    pip3 install -r requirements.txt --trusted-host nexus.lc.f-lab.tech
RUN rm requirements.txt

COPY . .

EXPOSE 8000

CMD ["bash", "-c", "python main.py"]