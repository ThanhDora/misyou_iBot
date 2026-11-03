FROM python:3.10-slim-bookworm

ARG IL2CPPDUMPER_VERSION=v6.7.46
ARG IL2CPPDUMPER_SHA256=db9bbbc538e33abfb057c7757ae5d6c1f16a05fdc0d13af8a5a67ea31faaba0c

# ffmpeg + .NET 8 runtime (Il2CppDumper-net6 runs on it via DOTNET_ROLL_FORWARD=Major)
RUN apt-get update -qq \
    && apt-get -y install --no-install-recommends ffmpeg curl ca-certificates unzip \
    && curl -sSL -o /tmp/ms.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/ms.deb && rm /tmp/ms.deb \
    && apt-get update -qq \
    && apt-get -y install --no-install-recommends dotnet-runtime-8.0 \
    && rm -rf /var/lib/apt/lists/*

ENV DOTNET_ROLL_FORWARD=Major \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Il2CppDumper (Linux, cross-platform .NET build) from the official release
RUN curl -sSL -o /tmp/il2cppdumper.zip \
        "https://github.com/Perfare/Il2CppDumper/releases/download/${IL2CPPDUMPER_VERSION}/Il2CppDumper-net6-${IL2CPPDUMPER_VERSION}.zip" \
    && echo "${IL2CPPDUMPER_SHA256}  /tmp/il2cppdumper.zip" | sha256sum -c - \
    && unzip -q /tmp/il2cppdumper.zip -d /app/dumper/Il2CppDumper-net6 \
    && rm /tmp/il2cppdumper.zip \
    && cp /app/dumper/config.json /app/dumper/Il2CppDumper-net6/config.json

# Command to run the application
CMD ["python", "bot.py"]
