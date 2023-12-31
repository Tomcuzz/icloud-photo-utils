# Start from the latest python base image
FROM python:3.11

# Set workspace
WORKDIR /src

#Copy the code into the conatiner
COPY /src .
COPY requirements.txt requirements.txt

# Define environment veriables
ENV TZ="Europe/London"

# Create Environment veriable logging level
ENV LOG_LEVEL="INFO"

#Make icloud directory
RUN mkdir /icloudpd

#Expose the nessasary volumes
VOLUME /icloudpd

#Update pip
RUN pip install --upgrade pip

#Install the Python dependancies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 to the outside world
EXPOSE 5000

# Create health check to check / url
HEALTHCHECK --interval=5m --timeout=3s --start-period=10s --retries=3 CMD curl -f http://localhost:8080/ || exit 1

# Command to run the executable
CMD ["flask", "run", "--host=0.0.0.0"]
