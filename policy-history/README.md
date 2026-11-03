# Historial de la política de privacidad

La política vigente está en [`../index.html`](../index.html). Cada versión anterior tiene una página HTML completa, enlazada desde el navegador de versiones que aparece en inglés y español.

<!-- POLICY_HISTORY_TABLE_START -->
| Versión de la app | Estado | Revisión | Política |
| --- | --- | --- | --- |
| 1.22 | Vigente | 3 de noviembre de 2026 | [Política actual](../index.html) |
| 1.21 | Archivada | 1 de noviembre de 2026 | [Política archivada](../version-1.21.html) |
| 1.20 | Archivada | 1 de noviembre de 2026 | [Política archivada](../version-1.20.html) |
| 1.15.3 | Archivada | 28 de octubre de 2026 | [Política archivada](../version-1.15.3.html) |
| 1.13 | Archivada | 9 de octubre de 2026 | [Política archivada](../version-1.13.html) |
<!-- POLICY_HISTORY_TABLE_END -->

## Actualizaciones para futuras versiones

Antes de publicar una nueva versión de Voltio en producción:

1. Revisa y actualiza en inglés y español las secciones que hayan cambiado en `index.html`.
2. Actualiza el valor de `<meta name="voltio-policy-version">`, las fechas de revisión y la versión indicada en el encabezado.
3. Publica ese cambio en `main` como parte del procedimiento de release.

La acción de GitHub compara la versión con el commit anterior. Cuando detecta un cambio, guarda una copia HTML íntegra de la política anterior, conserva las instantáneas existentes, actualiza la navegación de versiones de la página actual y de los archivos históricos, y reconstruye esta tabla. Las modificaciones de texto sin cambio de versión no crean una instantánea.

Google Play no emite un evento de release a este repositorio. Por eso, el cambio de la política y su versión debe entrar en `main` al preparar la release de Play; después, el archivado y la navegación se generan automáticamente en GitHub.
