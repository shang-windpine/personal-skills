# Stack Probes

Concrete search targets per technology. This is a lookup table, not a reading order — reach for the relevant section when a capability pass runs into a component, and for L0 when establishing basic conventions. Do not work through it top to bottom as a study plan.

## Project Skeleton

- Build graph: `pom.xml` (`<modules>`, `<dependencies>`), `build.gradle{,.kts}`, `settings.gradle`
- Entry point: `Main-Class`/`Main-Verticle` in `pom.xml` or manifest, `io.vertx.core.Launcher`, `public static void main`
- Local runtime: `docker-compose*.yml`, `Dockerfile`, `Makefile`, `.env*`, `scripts/`
- CI: `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml` — reveals the real build, test, and deploy contract
- Test layout: `src/test/java`, testcontainers usage, `*IT.java` vs `*Test.java`

## Vert.x

Vert.x has no annotation-scanned controller layer, so the usual Spring instincts do not apply. Structure is expressed through **Verticle deployment** and **EventBus addresses**, and those two maps are the backbone of the whole service.

**Verticle topology**
- `extends AbstractVerticle`, `implements Verticle`, `Deployable`
- `deployVerticle(`, `DeploymentOptions`, `setInstances(`, `setWorker(true)`, `setThreadingModel(`, `ThreadingModel.WORKER`
- `vertx.executeBlocking(`, `createSharedWorkerExecutor(`, `router.route().blockingHandler(`
- Startup order and dependency chaining: `Future.all(`, `CompositeFuture`, `.compose(` inside `start()`
- Clustering: `VertxOptions#setClusterManager`, Hazelcast/Infinispan/Zookeeper deps, `isClustered`

**EventBus — build an address registry**
- `eventBus().consumer(`, `.localConsumer(`, `.request(`, `.send(`, `.publish(`
- Address constants: interfaces or enums holding string literals; grep the literal prefixes once you find one
- Codecs: `registerDefaultCodec(`, `MessageCodec` — signals objects crossing the bus
- Service proxies: `@ProxyGen`, `@VertxGen`, `ServiceBinder`, generated `*VertxEBProxy` / `*VertxProxyHandler`

Record for each address: who consumes it, who sends to it, request/reply vs fire-and-forget, payload shape, and whether it is local-only or clustered. This table is effectively the service's internal API.

**HTTP surface**
- `Router.router(vertx)`, `router.route(`, `.get(`, `.post(`, `.put(`, `.delete(`
- `mountSubRouter(`, `route("/x/*").subRouter(`
- `BodyHandler.create()`, `CorsHandler`, `JWTAuthHandler`, `AuthenticationHandler`, `failureHandler(`
- OpenAPI: `RouterBuilder.create(`, `*.yaml`/`*.json` spec files
- `createHttpServer(`, `requestHandler(`, `.listen(`

**Scheduled and background work**
- `setPeriodic(`, `setTimer(`, `vertx.timerStream(`
- Quartz/`ScheduledExecutorService`, `@Scheduled`, cron expressions in config
- Kubernetes `CronJob` manifests, or a separate scheduler service invoking this one

These are whole capabilities with no request-driven entry point. Enumerate them early — they are the most commonly missed part of a service's behavior.

**Config**
- `ConfigRetriever.create(`, `ConfigStoreOptions`, `setType("file"|"env"|"sys"|"json")`
- Config files: `conf/*.json`, `*.yaml`, `application.conf`
- Note the **precedence order** — later stores override earlier ones, and this is a common source of confusion

**Async and failure semantics**
- `Future`, `Promise`, `.compose(`, `.recover(`, `.onFailure(`, `.otherwise(`
- Missing `.onFailure` on a returned Future means silently swallowed errors — worth flagging
- `CircuitBreaker`, retry helpers, timeouts in `DeliveryOptions#setSendTimeout`

## Redis

- Client: `Redis.createClient(`, `RedisAPI.api(`, `RedisOptions`, `setConnectionString(`, `RedisClientType.CLUSTER`
- Key naming: grep for string concatenation building keys, and for a central key-prefix constants class
- Cache vs lock vs queue vs pub-sub — determine which roles Redis actually plays:
  - Cache: `get`/`set`/`setex`/`expire`/`ttl`, and whether TTLs are always set
  - Distributed lock: `setnx`, `set ... NX PX`, Lua via `eval`, or Redisson `getLock`
  - Pub/sub: `subscribe`, `psubscribe`, `publish`
  - Counters/rate limiting: `incr`, `incrby`, sorted sets `zadd`/`zrangebyscore`
- Serialization format of values (JSON, protobuf, Java serialization) and who else reads them

## MongoDB

- Client: `MongoClient.create(`, `MongoClient.createShared(`, connection string in config
- Collection names: constants or literals in `getCollection(`, `find(`, `insert(`, `save(`, `bulkWrite(`
- Schema is implicit — infer document shape from writes, not reads, and note optional/legacy fields
- Indexes: `createIndex(`, `IndexOptions`, or migration scripts; missing indexes on queried fields are a real risk
- Aggregations: `aggregate(`, `$lookup`, `$match` — often where hidden business logic lives
- Transactions: `startSession(`, `withTransaction(` — rare in Mongo code, so note where it is used

## PostgreSQL

- Client: `PgPool` / `Pool.pool(`, `PgConnectOptions`, `PoolOptions#setMaxSize`
- Queries: `preparedQuery(`, `.execute(`, `SqlTemplate.forQuery(`, `RowMapper`, `Tuple.of(`
- Transactions: `withTransaction(`, `pool.getConnection(` + explicit `begin()`
- Migrations: `src/main/resources/db/migration/` (Flyway `V*__*.sql`), Liquibase `changelog*.xml` — **the schema history is the best available domain documentation**; read it early
- Blocking JDBC (`java.sql`, HikariCP, JDBI, MyBatis) inside a non-worker Verticle is an event-loop hazard — flag it

**The two-database question.** Worth answering once, early, because it recurs in every capability afterwards. Compare what PostgreSQL migrations define against what Mongo collections hold. Typically one is the transactional system of record and the other holds high-volume, flexible, or append-heavy data. State the rule you infer and cite the code that supports it. If any entity appears in both, find out which is authoritative and how they are kept consistent — that is usually the most fragile part of the system, and it will surface as a source of confusion in capability after capability until it is understood.

## RabbitMQ

- Client: `RabbitMQClient.create(`, `RabbitMQOptions`, or the raw `com.rabbitmq.client` `ConnectionFactory`
- Topology declarations: `exchangeDeclare(`, `queueDeclare(`, `queueBind(`, and the exchange/queue/routing-key constants
- Producers: `basicPublish(`, `AMQP.BasicProperties`, `setDeliveryMode(2)` for persistence
- Consumers: `basicConsumer(`, `handler(`, `QueueOptions#setAutoAck`, explicit `basicAck`/`basicNack`
- Reliability details worth capturing explicitly, since they determine failure behavior:
  - Ack mode — auto-ack silently drops messages on handler failure
  - Prefetch: `setMaxInternalQueueSize`, `basicQos`
  - Dead lettering: `x-dead-letter-exchange`, `x-dead-letter-routing-key`, `*.dlq` names
  - Retry/delay: `x-message-ttl`, `x-delayed-message` plugin, manual requeue loops
  - Idempotency — whether consumers can safely handle a redelivery, and how they dedupe
- Message payload contracts and which producer matches which consumer; a mismatch here is a common bug source

## Cross-Cutting

- Auth: `JWTAuth`, `OAuth2Auth`, token parsing, and where user identity is put on the routing context
- Observability: Micrometer/Prometheus registries, `MetricsOptions`, tracing (`OpenTelemetryOptions`, `ZipkinTracingOptions`), log config (`logback.xml`, `log4j2.xml`)
- Correlation IDs propagated across EventBus and MQ hops — or the absence of them
- Error mapping from exceptions to HTTP responses, and whether it is centralized
