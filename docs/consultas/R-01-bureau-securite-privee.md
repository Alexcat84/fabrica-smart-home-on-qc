# R-01 — Consulta al Bureau de la sécurité privée

**Estado: BORRADOR LISTO PARA ENVIAR. No enviado.**
Preparado el 2026-08-19. Quien lo envie rellena la fecha de envio en
`docs/POR-VERIFICAR-REGULATORIO.md` y archiva la respuesta.

Es la consulta que **bloquea toda venta en Quebec**. Va primero por eso, no por comodidad.

## Por que se pregunta en dos partes

La respuesta puede depender de si hay panel de intrusion, y esa distincion decide dos cosas
distintas del negocio:

- Si **sin panel** no hace falta licencia, el alcance actual del repositorio es vendible en Quebec de
  inmediato: camaras IP, sensores locales y sirena disuasoria gobernada por el sistema de
  automatizacion, sin central de monitoreo.
- Si **con panel** si hace falta, queda documentada la frontera que no se cruza, y se puede escribir
  en la declaracion de alcance del cliente sin ambiguedad.

Preguntar solo la primera mitad deja abierta la segunda, y alguien acabaria respondiendola por su
cuenta en obra. Preguntar las dos de una vez cuesta lo mismo.

## Datos a rellenar antes de enviar

| Campo | Valor |
|---|---|
| Razon social | _(rellenar)_ |
| Numero de empresa (NEQ) | _(rellenar)_ |
| Direccion | _(rellenar)_ |
| Persona de contacto | _(rellenar)_ |
| Correo y telefono | _(rellenar)_ |

## Texto a enviar (frances)

> Objet : demande d'avis écrit — obligation de permis d'agence pour l'installation de caméras IP et
> de capteurs locaux sans panneau d'intrusion et sans centrale de surveillance
>
> Madame, Monsieur,
>
> Nous préparons le lancement d'une entreprise d'intégration domotique résidentielle au Québec et
> nous souhaitons obtenir un avis écrit de votre part avant toute activité commerciale.
>
> **Description exacte de l'activité envisagée.** Nous installons, chez des particuliers, des
> caméras IP filaires et des capteurs locaux (contacts de porte et fenêtre, détecteurs de mouvement,
> capteurs de fuite d'eau, capteurs de température et d'humidité). L'enregistrement vidéo se fait
> exclusivement sur un serveur appartenant au client et situé dans sa propriété. Les alertes sont
> transmises uniquement au propriétaire et aux personnes qu'il désigne. **Aucun signal n'est transmis
> à une centrale de surveillance, aucun service d'urgence n'est dépêché par le système, et
> l'entreprise n'exploite ni centrale de surveillance ni service de répartition.** Le système exclut
> explicitement toute fonction de sécurité des personnes : aucune détection d'incendie, de fumée, de
> gaz ou de monoxyde de carbone, et aucune alerte médicale.
>
> **Première question.** Dans ce cadre — installation de caméras IP et de capteurs locaux, **sans
> panneau d'alarme d'intrusion et sans raccordement à une centrale de surveillance** — l'entreprise
> doit-elle détenir un permis d'agence en sécurité privée au sens de la Loi sur la sécurité privée ?
>
> **Seconde question.** La réponse change-t-elle si l'installation comprend **un panneau d'alarme
> d'intrusion et une sirène locale**, toujours **sans raccordement à une centrale de surveillance**
> et sans transmission de signal à un tiers ?
>
> Nous vous serions reconnaissants de bien vouloir nous transmettre votre réponse **par écrit**, afin
> que nous puissions la verser à notre dossier de conformité et nous y conformer dès le départ.
>
> Nous demeurons à votre disposition pour toute précision sur la nature technique de l'installation.
>
> Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.
>
> _(signature, fonction, coordonnées)_

## Que hacer con la respuesta

| Respuesta | Consecuencia inmediata |
|---|---|
| **No hace falta licencia en ninguno de los dos casos** | Se archiva la respuesta y se cita en la declaracion de alcance. Se puede vender en Quebec. La respuesta escrita es la defensa si alguien lo cuestiona despues |
| **No hace falta sin panel, si con panel** | Se archiva, y el panel de intrusion queda **fuera del alcance** de forma explicita en `catalogo/excluidos.yaml` y en la declaracion de alcance |
| **Hace falta en ambos casos** | **Se detiene la venta en Quebec.** Se abre R-02 (permiso de agente: coste, antecedentes, plazos) y se recalcula el plan financiero con ese coste y ese calendario |
| **Respuesta ambigua** | La fila sigue abierta. Se repregunta con el caso concreto por escrito. **No se interpreta a favor** |
