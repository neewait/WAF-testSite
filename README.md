# WAF+Site для тестирования атак на WEB сервисы

Для улучшения качества защиты **веб-приложений** и повышения точности обнаружения атак был разработан специализированный тестовый стенд WAF+Site. Это намеренно уязвимый ресурс, предназначенный для генерации событий ИБ и отработки механизмов детектирования.

Площадка позволяет нам в контролируемых условиях проводить симуляцию атак, собирать данные для написания и калибровки правил корреляции, а также пополнять базу знаний команды актуальными сценариями веб-атак.


Инструкция по установке:
--

**1. Скачиваем WAF `modsecurity` с гитхаба по ссылке**
```
https://github.com/coreruleset/modsecurity-crs-docker/tree/main 
```
Для того, чтобы можно было удобно развернуть сам WAF и сайт в дальнейшем, рекомендуется все устанавливать и настраивать в папке `/opt` для того, чтобы можно было удобно при необходимости:
- Удалить проект;
- Сделать резервную копию;
- Не засорять основные папки и пути;
- Простота поиска вашего проекта.

**2. Развертывание сайта**
Далее нам необходимо развернуть сайт, который мы будем атаковать. Рекомендуется сделать несколько пользователей с разными правами доступа к сайту, например `администратора` и `оператора`. 
Развернуть условную чувствительную базу данных и/или дополнительные артефакты, к которым мы будем пытаться стремиться, эксплуатируя различные сценарии атак.

Сам сайт можно развенуть самому или найти в открытых репозиториях готовую сборку.
Пример готовой сборки сайта, которую можно скачать используя `git clone`:
```
git clone https://github.com/neewait/WAF-testSite/tree/master
```

Также рекомендуется перед запуском и сборки WAF+Site расположить `WAF` и `сайт` следующим образом:
```
❯ tree
.
├── app
│   ├── app.py
│   ├── config.py
│   ├── data
│   ├── database
│   │   └── init_db.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── logs
│   ├── models.py
│   ├── requirements.txt
│   ├── static
│   │   ├── css
│   │   ├── img
│   │   └── js
│   ├── templates
│   │   ├── admin
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── errors
│   │   ├── login.html
│   │   ├── operator
│   │   ├── search.html
│   │   └── sensitive.html
├── containerd
│   ├── bin
│   └── lib
└── waf
    ├── docker-bake.hcl
    ├── docker-compose.yaml
    ├── LICENSE
    ├── logs
    ├── nginx
```

В папке `/opt` рядом лежат `WAF` и `сайт`.

**3. Настройка docker контейнеров**

Для того, чтобы связать наш `WAF` и `сайт`, рекомендуется использовать контейнеры. Также если разворачивать `WAF` сразу в **docker**, то его установка и настройка будет значительно легче.

Для **docker** контейнеров предлагается использовать следующие **IP-адреса**

```
{
    "default-address-pools":
    [
        {"base":"172.30.0.0/16","size":24},
        {"base":"172.31.0.0/16","size":24},
        {"base":"172.32.0.0/16","size":24},
        {"base":"172.33.0.0/16","size":24},
        {"base":"172.34.0.0/16","size":24},
        {"base":"172.35.0.0/16","size":24}
    ]
}
```

Пример конфигураций docker для `WAF` и для `сайта`:

Конфигурация `docker-compose.yaml` для WAF:
```
# This docker-compose file starts owasp/modsecurity-crs
x-defaults: &default-settings
  environment:
    SERVERNAME: localhost
    PARANOIA: 1
    BLOCKING_PARANOIA: 1
    ANOMALY_INBOUND: 5
    ANOMALY_OUTBOUND: 4
    REPORTING_LEVEL: 2

  volumes:
    - ./REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf:/etc/modsecurity.d/owasp-crs/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf
    - ./RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf:/etc/modsecurity.d/owasp-crs/rules/RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf

services:
  crs-nginx:
    image: owasp/modsecurity-crs:nginx
    container_name: modsecurity-waf
    restart: unless-stopped
    ports:
      - "8080:8080"
    
    <<: *default-settings
    
    environment:
      - BACKEND=http://securetest-app:5000
      - MODSEC_RULE_ENGINE=On
      - MODSEC_AUDIT_ENGINE=RelevantOnly
      - MODSEC_AUDIT_LOG=/var/log/modsec_audit.log
    
    volumes:
      - ./logs/modsec_audit.log:/var/log/modsec_audit.log
      - ./logs/access.log:/var/log/nginx/access.log
      - ./logs/error.log:/var/log/nginx/error.log
    
    networks:
      - securetest-net

networks:
  securetest-net:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.31.0.0/24
          gateway: 172.31.0.1
    name: securetest-net
```

Конфигурация `docker-compose.yml` для сайта:
```
version: '3.8'

services:
  securetest-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: securetest-app
    restart: unless-stopped
    expose:
      - "5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=change-me-in-prod-super-secret-key-123
    volumes:
      - ./logs:/opt/app/logs
      - ./data:/opt/app/data
    networks:
      - securetest-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

networks:
  securetest-net:
    external: true
    name: securetest-net

volumes:
  app-tmp:
```

После того, как мы прописали две этих конфигурации, необходимо запустить два этих контейнера. Для этого используются следующие команды:

```
# Проверка статуса Docker
sudo systemctl status docker

# Если не запущен — стартуем
sudo systemctl start docker

# Добавить в автозагрузку (опционально)
sudo systemctl enable docker

#запуск контейнера waf
cd /opt/waf
docker compose up -d

#запуск контейнера сайта
cd /opt/app
docker compose up -d --build

# Краткий список всех контейнеров
docker ps

# Все контейнеры (включая остановленные)
docker ps -a

# Только наши контейнеры с форматированием
docker ps --filter "name=modsecurity-waf" --filter "name=securetest-app" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Подробная информация о контейнере
docker inspect modsecurity-waf | head -50
docker inspect securetest-app | head -50

# Список Docker-сетей
docker network ls

# Детали нашей сети
docker network inspect securetest-net

# IP-адреса контейнеров в сети
docker network inspect securetest-net --format='{{range $k, $v := .Containers}}{{printf "%s -> %s\n" $k .IPv4Address}}{{end}}'

# Проверка связи внутри сети WAF и сайта
docker exec modsecurity-waf curl -s -o /dev/null -w "WAF→App: %{http_code}\n" http://securetest-app:5000/health

# Проверка связи:
docker exec securetest-app curl -s -o /dev/null -w "App→self: %{http_code}\n" http://localhost:5000/health

# Порты на хосте
sudo ss -tulpn | grep -E '8080|5000'

# Порты внутри контейнера WAF
docker exec modsecurity-waf ss -tulpn

# Порты внутри контейнера сайта
docker exec securetest-app ss -tulpn
```

**4. Взаимодействие с сайтом**

Далее если мы захотим перейти на сайт, то в браузере прописываем:
```
http://IP-адрес машины на которой хостится наш сайт:порт, который мы пробросили на выход в сеть по которому мы можем зайти на сайт
#пример
http://172.16.40.16:8080/
```

После этого мы попадаем на сайт и логинимся по кредам, которые мы прописали в коде или которые хранятся например в БД, которая может быть примонтирована к сайту.

**5. Тестирование на проникновение**

После того, как мы подняли сайт, мы можем приступать к тестированию на проникновение и эксплуатировать тактики, которые могут обходить `WAF`.
Их можно делать прямиком на сайте, в терминале устройства, на котором мы подключились к сайту или на сервере, где хостится сам сайт.

Самые интересные попытки атаки и их команды с атаками будут дополняться на **этой** страничке.

Вектора атак на WAF
--
