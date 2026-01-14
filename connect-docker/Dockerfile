# En güncel ve kütüphanelerin çoğu içinde olan imaj
FROM confluentinc/cp-kafka-connect:7.6.1

USER root

# Gerekli bileşenleri kur (İnternet hatasına karşı daha dayanıklı yöntem)
RUN confluent-hub install --no-prompt debezium/debezium-connector-postgresql:2.5.4
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-avro-converter:7.6.1

USER 1000