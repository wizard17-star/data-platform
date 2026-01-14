FROM eclipse-temurin:17-jre

ARG SPARK_VERSION=3.5.3
ARG HADOOP_PROFILE=hadoop3

RUN apt-get update && apt-get install -y \
    curl python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Spark binary
RUN curl -L -o /tmp/spark.tgz https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-${HADOOP_PROFILE}.tgz \
 && tar -xzf /tmp/spark.tgz -C /opt \
 && mv /opt/spark-${SPARK_VERSION}-bin-${HADOOP_PROFILE} /opt/spark \
 && rm /tmp/spark.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${SPARK_HOME}/sbin:/usr/bin:${PATH}"

# python libs
RUN pip3 install --no-cache-dir --break-system-packages pyspark==${SPARK_VERSION}

WORKDIR /opt

CMD ["spark-submit", "--version"]
