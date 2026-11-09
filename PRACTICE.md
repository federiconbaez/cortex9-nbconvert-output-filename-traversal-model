# Guía práctica (7 niveles)

Ejercicios **offline y locales** sobre cadenas de ruta. No hace falta
nbconvert ni red. Cada respuesta está comprobada en `tests/test_model.py`
(`test_practice_level_N`).

**Alcance:** practica solo en tu propia máquina, en un laboratorio propio
(VM o contenedor local) o en máquinas de HTB/plataformas de práctica donde
tengas autorización expresa. Nunca contra notebooks, servidores o usuarios
de terceros.

Comando: `PYTHONPATH=src python3 -m nbconvert_model case pre|post '<nombre>' [ext] [dir]`.

**Básico**

1. **El camino normal.** `img.png` con `nb_files`. ¿Dónde queda?
   (`/sandbox/build/nb_files/img.png`)
2. **Dos niveles arriba.** `../../evil.txt` en `pre`. ¿Dónde termina y por
   qué se agrega `.png`? (`/sandbox/evil.txt.png`; líneas 26-27 del diff)

**Intermedio**

3. **Ruta absoluta.** `/abs/x` en `pre`. ¿Por qué `join` descarta el
   directorio? (`/abs/x.png`)
4. **El fix.** El nombre del PoC del GHSA en `post`. ¿Qué queda y se avisa?
   (`PWNED.png`, aviso = 1, líneas 10-12 y 19-25)
5. **Basename vacío.** `../../../tmp/` en `post`. (`SKIP`, líneas 13-18)

**Avanzado**

6. **El borde del modelo.** `..` con `ext = "."` en `post`. ¿Dónde queda y
   por qué no es un hallazgo? (el propio build dir, `ESCAPE_FILES_DIR`;
   observación no verificada)
7. **Windows.** `..\..\evil` en `post` sobre POSIX. ¿Por qué queda dentro y
   qué tendrías que comprobar en tu propio Windows de laboratorio para
   saber qué pasa con `ntpath`? (`INSIDE`; no verificado en Windows)

**Defensa propia:** escribí para tu propio extractor una función que
rechace (en vez de recortar) nombres con separadores, compruebe la ruta
resuelta contra el directorio destino y pase el corpus de
`tests/test_model.py`. Agregá un caso a `fixtures/cases.tsv` con su
etiqueta a mano, regenerá `fixtures/expected.tsv` y comprobá que todo
coincide.
