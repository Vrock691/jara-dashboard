# HTML vers PNG

`main.py` rend une page HTML locale avec WeasyPrint, puis exporte l'image de la balise `<body>` en BMP 24 bits. Par défaut, le fichier est créé dans `screen-controlleur/pic` à la racine du dépôt ; le dossier est créé automatiquement. Les liens relatifs vers les feuilles CSS et les polices locales sont résolus à partir de l'emplacement du fichier HTML.

Le rendu dépend des fonctionnalités HTML/CSS prises en charge par WeasyPrint. Ce script ne lance pas JavaScript et n'a besoin ni de Chrome ni de Chromium.

## Installation

```sh
python3 -m pip install -r requirements.txt
```

WeasyPrint a aussi des dépendances système liées à Pango et à ses bibliothèques de rendu. Il faut qu'elles soient disponibles dans l'environnement Python d'Ubuntu Core.

## Utilisation

```sh
python3 main.py ./layout/layout.html
```

La sortie par défaut est `screen-controlleur/pic/layout.bmp`. Les options `--width` et `--height` définissent le viewport CSS utilisé pour la mise en page ; l'image est ensuite recadrée aux dimensions calculées de `<body>`.

```sh
python3 main.py --out ./captures --width 800 --height 600 ./layout/layout.html
```
