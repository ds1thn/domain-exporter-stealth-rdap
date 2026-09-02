# domain-exporter-stealth-rdap

Вспомогательный сервис для доменных TLD, чей RDAP-сервер работает, но не зарегистрирован в официальном bootstrap-реестре IANA (data.iana.org/rdap/dns.json) — т.н. stealth RDAP.

Из-за этого caarlos0/domain_exporter не может найти сервер для таких доменов и падает с ошибкой no whois server found for ... (WHOIS для этих TLD уже отключён регистратором).

Известные TLD с таким поведением на бэкенде Identity Digital: .me, .io, .sh. Сервис бьёт напрямую в https://rdap.identitydigital.services/rdap/domain/{domain}, минуя bootstrap.

# Пример прямого запроса для проверки вручную:
```bash
https://rdap.identitydigital.services/rdap/domain/t.me
```

# Сборка образа
```yaml
services:
  stealth_rdap_exporter:
    build: ./docker
    ports:
      - "9223:9223"
    restart: unless-stopped
```
# Деплой в Swarm
```yaml
services:
  domain_exporter_rdap:
    image: "docker.io/pan1c/domain-exporter-stealth-rdap:0.0.1"
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.labels.server_type == tech
      resources:
        limits:
          memory: 128M
```
# Проверка
```bash
curl "http://domain_exporter_rdap:9223/probe?target=t.me"
```
Должно вернуть что-то вроде:

    domain_expiry_days{domain="t.me"} 347

    domain_probe_success{domain="t.me"} 1

# Prometheus
```yaml
  - job_name: domain-me
    metrics_path: /probe
    scrape_interval: 3600s
    scrape_timeout: 30s
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: domain_exporter_rdap:9223
      - target_label: location
        replacement: "europe"
    static_configs:
      - targets:
          - t.me
          # добавляйте сюда домены на .me / .io / .sh по мере необходимости
```
Важно: job называется domain-me, а не domain. Алерты ниже матчат job="domain" — либо приводите job к одному имени с основным domain_exporter, либо заводите отдельный набор алертов с job="domain-me" (см. ниже).

# Alerts

Существующие правила используют job="domain", поэтому для job'а domain-me нужен либо тот же job_name, либо отдельные копии правил. Ниже — универсальный вариант без жёсткой привязки к job, покрывающий оба экспортера сразу:

# Grafana
Дашборд в grafana/dashboard.json
