# inventory-bl-scanner-webapp
Webapp with scanner to process deliveries and inventories 


### TO-DO:
<strong>lobby :</strong>
<br>[x] add supplier name to lobby tables and purchases option selector
<br>[ ] add QR CODE generator.
<br>[ ] ( optionnal ) add history table with recently validated purchases

<strong>room :</strong>
<br>[ ] make product selector only for flagged items.
<br>[ ] modify product qty data order ( 1- pkg; 2- qty, 3- received ). ( optionnal ) qty received all time visibility ?
<br>[ ] finish design of laser scanner modal
<br>[X] POST purchase method: while testing input, gather suspicious object to display error sources when tests are not passed. create display event.
<br>[ ] ( optionnal ) create new color for flagged wrong items ( == mostly scanner error bringing erroneous barcode )
<br>[ ] adjust CSS !

<strong>Users :</strong>
<br>[ ] review path system for non registered users ( add pw ? )
<br>[ ] increase security

<strong>logs :</strong>
<br>[ ] add logs!

<strong>inventaire :</strong>
<br>[ ] build all backend!

<strong>bug known :</strong>
<br>[ ] empty product object in addition to real scanned object, when laser scanning
<br>[ ] received qty sometimes desepearing sometimes...

<strong>documentation :</strong>
<br>[ ] add doc to most methods
<br>[ ] add typing hints
