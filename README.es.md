# cortex9-nbconvert-output-filename-traversal-model

Modelo de resolución de rutas de **CVE-2026-114140** (GHSA-pjvx-prjx-h659),
el path traversal en `ExtractOutputPreprocessor` de nbconvert
(`nbconvert/preprocessors/extractoutput.py`): el nombre de archivo de salida
tomado de `out.metadata["filename"]` del notebook se usaba tal cual, así que
`../../x` o `/abs/x` podían dejar una salida extraída fuera del directorio de
salida. Corregido en nbconvert 7.17.2 con el commit ce4bd99aec31 (`pre` =
antes, `post` = después).

Educativo, offline, determinista y solo con la biblioteca estándar de
Python. No se instala ni se ejecuta nbconvert, no se convierte ningún
notebook y los únicos archivos escritos están dentro de un sandbox de
`tempfile` en un test.

## Qué cambia el fix (líneas del diff guardado)

| Líneas | pre | post |
|---|---|---|
| 8 (contexto) | `filename` vacío o ausente → nombre por defecto | igual |
| 9 (eliminada) | `filename = out.metadata["filename"]` sin cambios | — |
| 10-12 (agregadas) | — | `os.path.basename(fname)` |
| 13-18 (agregadas) | — | basename vacío → aviso y se salta |
| 19-25 (agregadas) | — | aviso si se quitaron componentes |
| 26-27 (contexto) | agrega `ext` si falta | igual |

La unión de `output_files_dir` con el nombre sigue el advisory y el test
nuevo (línea 54 del diff). Ponerla bajo el directorio de build
(`/sandbox/build`, una cadena simbólica) es una **suposición del modelo**.

## Evidencia diferencial

Los 9 positivos escapan en `pre` y quedan `INSIDE` o `SKIP` en `post`; los
5 negativos no cambian de etiqueta. En un corpus de 9.360 nombres
generados, `post` nunca sale del directorio de build y, con una extensión
real (`.png`), nunca sale de `output_files_dir`. Detalle en
`results/differential.csv`, con las líneas del diff que deciden cada fila.

**Borde del modelo, no verificado:** con el nombre `..` y `ext == "."`, `post`
conserva `..` y el destino es el propio directorio de build (`a02`). Sigue
dentro del build, no se comprobó si nbconvert puede producir esa `ext` y no
es un hallazgo.

## Uso

```sh
python3 tests/run.py
python3 scripts/derive_expected.py | diff - fixtures/expected.tsv
PYTHONPATH=src python3 -m nbconvert_model results fixtures/cases.tsv /tmp/r && diff -r results /tmp/r
```

Ejercicios en [PRACTICE.md](PRACTICE.md); límites en
[LIMITATIONS.md](LIMITATIONS.md); fuentes en [SOURCES.md](SOURCES.md).
Licencia: Apache-2.0.
