# Entrada para Android (buildozer). Usa juego.lataM incluido; si no hay, muestra el selector.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lataM
lataM.main()
