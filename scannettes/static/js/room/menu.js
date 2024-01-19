

///////////////////////////// MENU BUILDER

class MenuFactory {
    constructor(payload) {
        this.infosContainer(payload);
        this.actionsContainer(payload);
    }

    infosContainer(payload) {
        let container = document.getElementById("info");
        container.appendChild(this.nameBuilder(payload.name, payload.rid));
        container.appendChild(this.typeBuilder(payload.type));
        container.appendChild(this.oidBuilder(payload.type, payload.oid));
        if (payload.type === "purchase") {
            container.appendChild(this.supplierBuilder(payload.supplier));
        }
        container.appendChild(this.dateBuilder(payload.creating_date));
        container.appendChild(this.stateBuilder(payload.state));
    }

    actionsContainer(payload) {
        let container = document.getElementById("actions");

        // container.appendChild(this.btnBuilder("Terminer", "confClosing()"));
        // container.appendChild(this.btnBuilder("Réinitialiser", "confReInit()"));
        // container.appendChild(this.btnBuilder("Recharger", "confRebase()"));
        // container.appendChild(this.btnBuilder("Valider", "confValidate()"));
        // container.appendChild(this.btnBuilder("Nullifier", "confNullify()"));
        if (admin === false & payload.state === "open") {
            container.appendChild(this.btnBuilder("Terminer", "confClosing()"));
            this.rmSupr()

        } else if (admin === true & payload.state === "open" & payload.type === "purchase") {
            container.appendChild(this.btnBuilder("Terminer", "confClosing()"));
            container.appendChild(this.btnBuilder("Réinitialiser", "confReInit()"));
            container.appendChild(this.btnBuilder("Recharger", "confRebase()"));

        } else if (admin === true & payload.state === "close" & payload.type === "purchase") {
            container.appendChild(this.btnBuilder("Valider", "confValidate()"));

        } else if (admin === true & payload.state === "open" & payload.type === "inventory") {
            container.appendChild(this.btnBuilder("Terminer", "confClosing()"));

        } else if (admin === true & payload.state === "close" & payload.type === "inventory") {
            container.appendChild(this.btnBuilder("Nullifier", "confNullify()"));
            container.appendChild(this.btnBuilder("Valider", "confValidate()"));

        } else if (payload.state === "done") {
            document.getElementById("camera").remove();
            document.getElementById("laser").remove();
            this.rmSupr()
        }
    }

    btnBuilder(text, onclick) {
        let btn = document.createElement("button");
        btn.classList.add("btn-small", "border", "stack");
        btn.innerText = text;
        btn.setAttribute("onclick", onclick);
        return btn;
    }

    infoBuilder(content) {
        let info = document.createElement("p");
        info.innerHTML = content;
        return info;
    }

    nameBuilder(name, rid) {
        let content = "<strong>Salon : </strong>";
        if (name === "") {
            name = "Salon n° " + rid;
        }
        content = content + name;
        return this.infoBuilder(content);
    }

    typeBuilder(type) {
        let content;
        if (type === "purchase") {
            content = "<strong>Type : </strong>Commande";
        } else if (type === "inventory") {
            content = "<strong>Type : </strong>Inventaire";
        }
        return this.infoBuilder(content);
    }

    oidBuilder(type, oid) {
        let content;
        if (type === "purchase") {
            content = "<strong>Commande : </strong>" + oid;
        } else if (type === "inventory") {
            content = "<strong>Inventaire : </strong>" + oid;
        }
        return this.infoBuilder(content);
    }

    supplierBuilder(fname) {
        let content = "<strong>Fournisseur : </strong>" + fname;
        return this.infoBuilder(content);
    }

    stateBuilder(state) {
        let content;
        if (state === "open") {
            content = "<strong>Statut : </strong> réception";
        } else if (state === "close") {
            content = "<strong>Statut : </strong> vérification";
        } else if (state === "done") {
            content = "<strong>Statut : </strong> archivé";
        }
        return this.infoBuilder(content);
    }

    dateBuilder(date) {
        let content = "<strong>Date : </strong>" + date;
        return this.infoBuilder(content);
    }

    rmSupr() {
        let nodes = document.getElementsByClassName("del");
        Array.from(nodes).forEach(function(node) {
            node.remove();
        });
    }
}
