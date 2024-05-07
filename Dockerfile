FROM python:3.13.0a6-slim-bookworm

RUN apt-get update
RUN apt-get -y install sudo curl lsb-release gnupg

RUN curl https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" | sudo tee /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update
# RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18
# RUN echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
# RUN apt-get install -y unixodbc-dev
# RUN apt-get install -y libgssapi-krb5-2

# ENV PYTHONUNBUFFERED=1 
# WORKDIR /usr/src/app
# COPY requirements.txt ./

# RUN rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]

# RUN pip install --upgrade pip
# RUN pip install numpy
# RUN pip install -r requirements.txt