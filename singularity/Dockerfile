FROM ubuntu:14.04

RUN apt update && apt install -y wget

ENV META_UID 2556
ENV META_USER sustrmic
RUN useradd -m -u $META_UID $META_USER


WORKDIR /app
RUN echo "#!/bin/bash\nwget http://35.157.85.16:8888/\n" > entrypoint.sh
RUN chmod +x entrypoint.sh

RUN chown $META_USER -R /app
RUN chgrp $META_USER -R /app

USER $META_USER
#ENTRYPOINT ["./entrypoint.sh"]

#WARNING: Non existent bind point (directory) in container: '/afs'
#WARNING: Non existent bind point (directory) in container: '/auto'
#WARNING: Non existent bind point (directory) in container: '/scratch'
#WARNING: Non existent bind point (directory) in container: '/storage'
#WARNING: Could not chdir to home: /storage/brno2/home/sustrmic
