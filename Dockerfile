FROM nvidia/cuda:12.8.1-base-ubuntu22.04

# Set noninteractive mode
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    gnupg \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# # Install CUDA tools
RUN apt-get update && apt-get install -y \
    cuda-nvcc-12-8 \
    cuda-cudart-dev-12-8 \
    cuda-libraries-dev-12-8


# Add CUDA to PATH and LD_LIBRARY_PATH
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Set Python alias
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install Python dependencies
COPY code/requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

# Copy the code to the app directory
COPY ./code /app

# Expose port
EXPOSE 8000

# Run FastAPI server
ENTRYPOINT ["./entrypoint.sh"]
