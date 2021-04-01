FROM python:slim

COPY . scbw

RUN    apt-get update \
	&& apt-get install -qy curl \
	&& curl -sSL https://get.docker.com/ | sh\
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install scbw/
CMD ["scbw.play"]

