# Especificación del modelo (destilado de la memoria)

Resumen fiel de `docs/Memoria_San_Mames-2.pdf` (Parte 1). **Si hay conflicto,
manda la memoria.** Entre corchetes, la clave correspondiente de
`configs/base.json`.

## 1. Sistema y alcance

* Caso: San Mamés (Bilbao). Aforo oficial 53.331 [F1]. Partido de referencia
  Athletic–Manchester United: **48.775 pasos por torno**, 24 puertas [F2].
  Apertura **90 min** antes del inicio [F3].
* Sistema **dinámico, estocástico, discreto y terminante**: una réplica = un
  partido, de la apertura de puertas a la salida del último espectador.
* 4 fases: **acceso** (cola y torno, ≈ 4 s por paso, 15 pers/min por torno),
  **ubicación** (camino al vomitorio, asiento, acomodadores), **permanencia**
  (90 min de juego + 15 de descanso), **salida** (salidas de la macrozona con
  capacidad por anchura).
* Simplificación: **4 macrozonas** A, B, C, D (una por tribuna). Cada una:
  **6 puertas**, **10 bloques** con su vomitorio, **6 salidas**. Bloques 1–5 =
  grada inferior, 6–10 = grada superior; comparten las salidas de su macrozona.

**Dentro:** llegadas, colas y tornos; desplazamiento y vomitorios; salida
ordinaria; incidencias (conflicto por asiento, fallo de lectura, avería de
torno, cierre de puerta); evacuación de emergencia.
**Fuera:** recorrido exterior hasta la puerta; bares, aseos y descanso; VIP y
afición visitante; interacción física entre peatones; transporte y cacheos.

### Requisitos funcionales

| ID | Requisito |
|---|---|
| RF01 | Leer de un fichero de configuración todos los parámetros. |
| RF02 | Generar las llegadas a partir de un perfil por franjas de 15 min. |
| RF03 | Recursos de capacidad limitada, colas FIFO y prioridad no expulsiva opcional. |
| RF04 | Encadenar entrada, permanencia y salida manteniendo la identidad del espectador. |
| RF05 | Activar o desactivar cada incidencia de forma independiente. |
| RF06 | Réplicas con semillas registradas y exportación de indicadores por escenario. |

### Supuestos

* Cada entidad es un espectador individual; su hora de llegada es cuando se une
  a la cola de su puerta.
* Reparto igual entre macrozonas (25 %) y, dentro de cada una, igual entre
  puertas y bloques.
* **3 tornos por puerta** (72 en total) — hipótesis; se varía en X1.
* La prioridad **no interrumpe** un control iniciado; una avería **no interrumpe**
  un servicio en curso.
* Capacidad de salida: **66 pers/(m·min)** (Green Guide, escaleras) [F5]; la
  anchura (4 m) es hipótesis.
* El perfil de llegadas es una hipótesis inspirada en F2 (F2 registra paso por
  torno, no llegada a la cola).

## 2. Preguntas (P) y KPIs

| Código | Pregunta |
|---|---|
| P1 | Esperas, colas y utilización de tornos con la operativa actual; cuello de botella. |
| P2 | Tornos por puerta para que el **95 %** espere **< 10 min**. |
| P3 | Mejora de esperas y entradas tardías si parte del público adelanta su llegada. |
| P4 | Qué gana el colectivo priorizado (mayores y PMR) y cuánto pierde el resto. |
| P5 | ¿Reduce la cola en salidas que la grada superior salga unos minutos después? ¿A qué coste de tiempo total? |
| P6 | Retraso de los conflictos por asiento al resto del bloque; acomodadores necesarios. |
| P7 | Cierre de una puerta en hora punta: ¿lo absorbe la redirección? |
| P8 | Evacuación: tiempo de vaciado; ¿se cumple la referencia de **8 min** [F6]? ¿Y con una salida bloqueada? |

| KPI | Definición | Unidad | Preguntas |
|---|---|---|---|
| Espera media en cola | inicio del control − llegada a la cola | min | P1–P4, P7 |
| Percentil 95 de espera | espera que no supera el 95 % | min | P1–P4, P7 |
| Cola máxima por puerta | máximo de personas esperando a la vez | pers. | P1, P7 |
| Utilización de tornos | tiempo ocupado / tiempo disponible | % | P1, P2 |
| % entrada tardía por colas | de quienes llegan con t < 0, % que se sienta con t > 0 | % | P1–P4, P6 |
| Diferencia entre grupos | espera media priorizados − resto | min | P4 |
| Retraso por conflicto | espera extra en vomitorios con conflicto vs sin | s/pers. | P6 |
| Salida | última salida − final del partido; cola máxima en salidas | min / pers. | P5 |
| Evacuación | último en zona segura − alarma; % fuera a los 8 min | min / % | P8 |

Implementación de los KPIs: ver `docs/CONTRATOS.md`.

## 3. Lógica del modelo

### Fase A · Entrada
1. t = −90: puertas abiertas, colas vacías, recursos libres.
2. Se generan los N espectadores: hora de llegada, macrozona, puerta, bloque,
   grupo, velocidad, distancia al vomitorio.
3. A su hora se une a la cola de su puerta. Si está **cerrada** y la redirección
   está activa, va a la puerta de su macrozona **con menos cola**; si no, espera
   a que reabra.
4. Con un torno libre pasa el control; a veces la entrada no se lee y se repite.
5. Camina hasta su vomitorio y lo atraviesa. Si el asiento está ocupado
   (conflicto), espera a un acomodador **ocupando una plaza del vomitorio**
   mientras dura, ralentizando a los de detrás.
6. Al sentarse: tiempo de acceso y si ha entrado tarde.

### Fase B · Permanencia
t = 0 a t = +105. En emergencia se programa aquí la alarma.

### Fase C · Salida ordinaria
En t = +105 se libera la salida: **simultánea**, o **escalonada** (inferior
primero, superior **3 min** después). Cada espectador recorre la **misma
distancia** que en la entrada hasta la salida de su macrozona **con menos cola**,
espera si está saturada y sale.

### Fase D · Evacuación
La alarma **cierra los accesos**. Quien esté en una cola exterior abandona y
**no cuenta** en la evacuación. Salidas **+30 % de anchura**. Tras su tiempo de
reacción, cada espectador camina **un 20 % más rápido** a la salida de su
macrozona con menos cola. Variante con bloqueo: **una salida de la macrozona A**
inutilizada; su público se reparte entre las otras 5.

### Eventos principales

| Evento | Activación | Acciones |
|---|---|---|
| E0 Inicio de réplica | t = −90 | Crear recursos, contadores a cero, generar espectadores, programar fin del partido. |
| E1 Llegada | t = t_llegada(i) | Elegir puerta (estado y política) y unirse a su cola. |
| E2 Inicio de control | Torno libre y operativo; primero el de mayor prioridad | Ocupar torno, registrar espera. |
| E3 Fin de control | Fin del servicio (+ relectura) | Liberar torno, iniciar desplazamiento. |
| E4 Sentado | Atraviesa el vomitorio sin conflicto o se resuelve el conflicto | Registrar t_sentado y entrada tardía. |
| E5 Final del partido | t = +105 | Liberar la salida según la política. |
| E6 Paso por salida | Salida libre | Registrar t_salida, sumar a salidos. |
| E7 Alarma | t fijado por el experimento (+40) | Cerrar accesos, ampliar salidas, iniciar evacuación. |
| E8 Fin de evacuación | Último espectador en zona segura | Registrar tiempo de evacuación. |
| E9 Fin de réplica | Todos fuera/evacuados o tiempo máximo | Guardar estadísticos. |

### Incidencias (aportación propia)

| Incidencia | Activación | Efecto | Config |
|---|---|---|---|
| I1 Conflicto por asiento | Al llegar al asiento, **p = 0,5 %** | Ocupa una plaza del vomitorio hasta que un acomodador lo resuelve; **Triangular(1, 3, 10) min** | `incidents.seat_conflict` |
| I2 Fallo de lectura | En el torno, **p = 3 %** | Añade **Uniforme(5, 15) s** al servicio | `incidents.read_failure` |
| I3 Avería de torno | Tiempo entre fallos **Exponencial(media 240 min)** por torno | Cuando el torno queda libre, se para **Uniforme(3, 10) min** | `incidents.turnstile_failure` |
| I4 Cierre de puerta | **Puerta 1 de la macrozona A**, en **t = −30 min** (D31; la memoria decía +20), **10 min** | Nadie entra por ella; redirección o espera según escenario | `incidents.gate_closure` |

Probabilidades y duraciones son hipótesis (sin datos públicos); se revisan en S1.

### Ciclo de vida y conservación
Cada espectador está en un único estado. En todo momento:
**N = pendientes + en cola + en control + en tránsito + en conflicto + sentados + saliendo + fuera.**

### Flujo de datos
Config JSON por escenario → simulación (una fila por espectador con sus tiempos)
→ KPIs por réplica → comparación entre escenarios.

## 4. Variables

### Atributos (§4.1)
* **Espectador:** id, macrozona, puerta, bloque, grada (inferior/superior),
  grupo, velocidad, distancia, t_llegada, t_inicio_control, t_fin_control,
  t_sentado, t_salida, conflicto (sí/no), tardío (sí/no).
* **Incidencia:** tipo I1–I4, recurso afectado, t_inicio, t_fin.
* **Grupos:** 88 % estándar; 10 % mayores (velocidad × 0,8); 2 % PMR
  (velocidad × 0,5) [`groups`].

### Variables de estado (§4.2)
t (segundos; resultados en min respecto al inicio), fase
(Entrada/Partido/Salida/Evacuación), cola_puerta[p], tornos_ocupados[p],
tornos_averiados[p], puerta_abierta[p], plazas_vomitorio_ocupadas[b] (incluye
conflictos), conflictos_en_espera[z], cola_salida[s], dentro, salidos.

### Factores controlables (§4.3)

| Variable de decisión | Base | Niveles | Config |
|---|---|---|---|
| Tornos por puerta (c) | 3 | 2, 3, 4 (X1) | `turnstiles_per_gate` |
| Acomodadores por macrozona | 6 | 3, 6, 9 (X5; D33) | `stewards_per_zone` |
| Disciplina de cola en tornos | FIFO | FIFO, prioridad no expulsiva (X3) | `queue_discipline`, `priority_groups` |
| Política de salida | Simultánea | Simultánea, escalonada 3 min (X4) | `exit_policy`, `exit_stagger_min` |
| Redirección ante cierre | Activa | Inactiva, activa (X6) | `redirect_on_gate_closure` |
| Perfil de llegadas | Base | Base, anticipado (X2) | `arrival_profile` |

### Parámetros deterministas

| Parámetro | Valor | Config |
|---|---|---|
| N | 48.775 (aforo 53.331) | `n_spectators` |
| Reparto por macrozona | 25 % (12.194 pers.) | `zone_share` |
| Puertas | 24 (6 por macrozona) | `gates_per_zone` |
| Vomitorios | 10 por macrozona, 8 plazas | `blocks_per_zone`, `vomitory_capacity` |
| Salidas | 6 por macrozona, 4 m | `exits_per_zone`, `exit_width_m` |
| Tasa de paso en salida | 66 pers/(m·min) → 264 pers/min por salida | `exit_rate_per_m_min` |
| Apertura / inicio / final | −90 / 0 / +105 min | `t_open_min`, `t_start_min`, `t_end_min` |
| Evacuación | anchura × 1,3; velocidad × 1,2 | `emergency.exit_width_factor`, `emergency.speed_factor` |

### Variables aleatorias

| Variable | Distribución | Config |
|---|---|---|
| Hora de llegada | Franja según perfil + instante uniforme en ella | `arrival_profiles` |
| Servicio en torno | **Triangular(2, 4, 6) s** (media 4 s) | `service_time_s` |
| Velocidad | **Normal(1,45; 0,23) m/s truncada en [0,6; 2,2]** × factor del grupo | `speed_mps` |
| Distancia puerta → asiento | **Uniforme(60, 180) m** (la misma para salir) | `distance_m` |
| Paso por vomitorio | **Triangular(5, 10, 20) s** | `vomitory_pass_s` |
| Reacción a la alarma | **Triangular(30, 60, 120) s** | `emergency.reaction_s` |
| Incidencias | ver tabla I1–I4 | `incidents` |

Paso por salida **determinista**: 60/264 ≈ **0,23 s/pers** (4 m) o **0,17 s** en
evacuación (5,2 m).

### Perfil de llegadas

X2: un **30 %** de quienes llegarían en los últimos 30 min adelanta su llegada a
las franjas de −60 a −30 min.

| Franja (min) | Base % | Base pers/min | X2 % | X2 pers/min |
|---|---:|---:|---:|---:|
| −90 a −75 | 4 | 130 | 4 | 130 |
| −75 a −60 | 6 | 195 | 6 | 195 |
| −60 a −45 | 9 | 293 | 17,4 | 566 |
| −45 a −30 | 16 | 520 | 24,4 | 793 |
| −30 a −15 | 28 | 910 | 19,6 | 637 |
| −15 a 0 | 28 | 910 | 19,6 | 637 |
| 0 a 15 | 7 | 228 | 7 | 228 |
| 15 a 30 | 2 | 65 | 2 | 65 |

### Comprobación previa de capacidad (para validar)
* Torno: 4 + 0,03 × 10 = **4,3 s** (≈ 14 pers/min); operativo el 97 % → **13,6 pers/min**.
* 72 tornos ≈ **978 pers/min** vs 910 llegadas/min en punta → **ρ ≈ 0,93**.
  2 tornos/puerta: **ρ ≈ 1,40** (la cola crece sin parar). 4: **ρ ≈ 0,70**.
  Perfil X2: **ρ ≈ 0,65**.
* Vomitorios: 411 pers/min por macrozona frente a 245 que dejan pasar los
  tornos → no son cuello de botella salvo con conflictos.
* Salida ordinaria: **7,7 min** por macrozona solo para atravesar las salidas.
  Evacuación: **5,9 min** (**7,1 min** con una salida bloqueada) + reacción +
  recorrido → la referencia de 8 min queda en el límite.

### Variables de salida (§4.4)
* Por observación: espera W_i, acceso A_i, salida S_i, evacuación V_i,
  tardío δ_i → media, P95, proporción.
* Ponderadas en el tiempo: L_p(t), B_p(t), plazas de vomitorio →
  media temporal, máximo, utilización U = (1/cT)∫B(t)dt.
* Por réplica: Y_j (cada KPI en la réplica j) → media entre réplicas e IC.
  Las observaciones dentro de una réplica están autocorrelacionadas: la
  inferencia se hace sobre los Y_j.

### Recursos (§4.5) e implementación SimPy

| Recurso | Capacidad | Regla | SimPy |
|---|---|---|---|
| Tornos | 3 por puerta (72) | FIFO; X3: prioridad no expulsiva mayores y PMR | `PriorityResource(capacity=3)` por puerta |
| Vomitorios | 10 × 8 plazas por macrozona | FIFO; un conflicto ocupa plaza mientras dura | `Resource` |
| Acomodadores | 6 por macrozona | Por orden de llegada | `Resource` |
| Salidas | 6 × 4 m por macrozona | La de menos cola de su macrozona | `Resource` |

* Reloj: `simpy.Environment`, `env.now` en segundos.
* Espectador: un proceso generador por espectador; atributos en un dataclass.
* I3: proceso que pide el torno con **máxima prioridad** y lo retiene durante la
  reparación (nunca corta un servicio).
* I4: proceso que cambia `puerta_abierta[p]` y dispara un `simpy.Event` al reabrir.
* E7: proceso que interrumpe con `Process.interrupt()` a los sentados.
* Azar: `numpy.random.default_rng` con un generador independiente por fuente.
* Resultados: pandas; gráficas: matplotlib.

## 5. Diseño experimental

Se cambia **un solo factor** respecto a X0; mismas semillas en todos.

| Exp. | Escenario | Factor | Pregunta | Fichero(s) |
|---|---|---|---|---|
| X0 | Base: 3 tornos, FIFO, perfil base, salida simultánea, I1–I3 activas, sin cierre ni alarma | — | P1 | `X0_base` |
| X1 | 2 y 4 tornos por puerta | Capacidad de acceso | P2 | `X1_2tornos`, `X1_4tornos` |
| X2 | Llegada anticipada | Perfil de llegadas | P3 | `X2_anticipado` |
| X3 | Prioridad en torno para mayores y PMR | Regla de cola | P4 | `X3_prioridad` |
| X4 | Salida escalonada (superior +3 min) | Política de salida | P5 | `X4_escalonada` |
| X5 | Conflictos al 1 % con 3, 6 y 9 acomodadores (ampliación D33) | I1 y personal | P6 | `X5_3acomodadores`, `X5_6acomodadores`, `X5_9acomodadores` |
| X6 | Cierre de puerta sin y con redirección | I4 | P7 | `X6_sin_redireccion`, `X6_con_redireccion` |
| X7 | Alarma en t = +40 con todas las salidas y con una bloqueada | Emergencia | P8 | `X7_todas_salidas`, `X7_salida_bloqueada` |
| S1 | Sensibilidad sobre X0: N ±10 %, velocidad ±15 %, servicio ±25 % | Parámetros inciertos | P1–P8 (comprobación) | `S1_sensibilidad` (6 variantes) |

### Condiciones de ejecución

| Aspecto | Decisión |
|---|---|
| Tipo | Terminante: de t = −90 a la salida del último (≈ t = +115, unas 3 h 25 min). Límite de seguridad **6 h** (`max_sim_hours`). |
| Warm-up | No (el estadio vacío es el estado inicial real). |
| Réplicas | **10 piloto** por escenario; n = (t·s/h)² con IC 95 % y **h ≤ 5 % de la espera media**. Se prevén **≈ 30**. |
| Volumen | 12 configuraciones × 30 ≈ **360 ejecuciones** + S1. |
| Números aleatorios | **Mismas semillas** en todos los escenarios. |
| Análisis | Media ± t_{0,975; n−1}·s/√n de cada KPI e IC de la diferencia con X0. |

## 6. Verificación y validación

* **Conservación:** la suma de espectadores en todos los estados es siempre N.
* **Orden temporal:** t_llegada ≤ t_inicio_control ≤ t_fin_control ≤ t_sentado ≤ t_salida.
* **Capacidad:** ningún recurso supera su capacidad.
* **Casos límite:** con muchos tornos y sin incidencias, colas casi nulas; con 2
  tornos/puerta deben crecer en punta (ρ > 1); los tiempos de salida deben
  acercarse a la estimación de §4.3 (7,7 min).
* **Validación:** el ritmo de paso por torno debe coincidir con F2. Sin datos
  completos de colas ni salidas: resultados como **comparación entre
  escenarios**, no predicciones exactas.

## Referencias

F1 web oficial San Mamés · F2 García et al. (2026), *Simulation Modelling
Practice and Theory* 149, 103279 · F3 Athletic Club (2025), accesos · F4
documentación SimPy · F5 Green Guide, cap. 10 (egress) · F6 NI Assembly (2015),
evacuación 2,5–8 min · D1 guion de prácticas.
