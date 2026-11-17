# Guion del video de respaldo — Feature 4

Duración máxima: 3 minutos.

1. **Inicio (20 s):** abrir RutaPyme con el backend activo y mostrar la pantalla
   única: operación, cobertura, ruta y red dibujada.
2. **Red (35 s):** registrar los cinco puntos de la red de aceptación y las
   cuatro conexiones. Mostrar que el SVG distingue nodos, flechas y costos, y
   que la casa aislada no tiene conexiones.
3. **Cobertura (30 s):** consultar desde la bodega. Mostrar norte, centro y
   Casa A como alcanzables; la casa aislada no aparece.
4. **Ruta (35 s):** pedir Bodega→Casa A. Mostrar la ruta de 7 km por Norte y
   Centro, aunque existe una conexión directa de 9 km.
5. **Cambio F4 (30 s):** seleccionar Centro como parada obligatoria y repetir la
   consulta con `via`. Mostrar que la ruta contiene la parada y conserva el
   costo exacto.
6. **Errores (25 s):** mostrar una ruta inexistente como respuesta válida y un
   costo inválido con su mensaje; mencionar que un nodo inexistente devuelve
   `DESTINATION_NOT_FOUND`.
7. **Cierre (5 s):** mostrar `docs/evidencia-f4.txt` con el resumen de pruebas.

La grabación real debe hacerse sobre el frontend integrado; este archivo es el
guion reproducible y no sustituye el enlace final del video.
