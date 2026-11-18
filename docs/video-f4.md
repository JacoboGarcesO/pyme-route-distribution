# Guion del video de respaldo — Feature 4

Duración máxima: 3 minutos.

1. **Inicio (20 s):** abrir RutaPyme con el backend activo y mostrar la pantalla
   única: operación, cobertura, ruta y red dibujada.
2. **Red (35 s):** con la ciudad cargada (`python backend/load_new_city.py`),
   registrar un punto nuevo y su conexión. Mostrar en el mapa 3D las calles de
   doble sentido (línea amarilla), las de sentido único (señal UNA VÍA) y el
   costo pintado en cada calle.
3. **Cobertura (30 s):** consultar desde Bodega central. Mostrar los anillos
   verdes de los alcanzables y el rojo de Casa Finca El Mirlo, sin camino.
4. **Ruta (35 s):** pedir una ruta entre la bodega y un cliente y mostrar la
   explicación sobre el mapa: cada tramo con su costo y la suma total.
5. **Cambio F4 (30 s):** repetir con un cliente como parada obligatoria (la
   interfaz solo ofrece casas y bodegas como parada). Mostrar la parada marcada
   y abrir el seguimiento 3D: el camión entrega en la parada y luego en B.
6. **Errores (25 s):** mostrar una ruta inexistente como respuesta válida y un
   costo inválido con su mensaje; mencionar que un nodo inexistente devuelve
   `DESTINATION_NOT_FOUND` (cubierto por el script de aceptación).
7. **Cierre (5 s):** mostrar `docs/evidencia-f4.txt` con el resumen de pruebas.

La grabación real debe hacerse sobre el frontend integrado; este archivo es el
guion reproducible y no sustituye el enlace final del video.
