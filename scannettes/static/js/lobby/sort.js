
function tableSort(elm) {
    let selected = elm.getElementsByClassName("order")[0];
    new TableSorter(selected);
}


class TableSorter {
    constructor(sel) {
        let symbols = {"neu": "-", "asc": "▼", "des": "▲"};
        let reversedSymbols = {"-": "neu", "▼": "asc", "▲": "des"};
        let orders = {"neu": "asc", "asc": "des", "des": "asc"};


        let currentSelector = sel.id;
        let currentSortingState = reversedSymbols[sel.innerText];
        let nextSortingState = orders[currentSortingState];
        let nextSymbol = symbols[nextSortingState];

        let [nodesRef, valuesRef] = this.collectNodes(currentSelector);
        if (valuesRef.length == 0) {
            return;
        }
        let sorted = this.sort(nextSortingState, valuesRef);
        this.inject(sorted, nodesRef);
        this.modifySortingStates(currentSelector, nextSymbol);
    }


    collectNodes(selid) {
        let stateValues = {"open": 1, "close": 2, "done": 3};
        const table = document.getElementById("room-table");
        let nodes = table.getElementsByClassName("purchase");

        let nodesRef = {};
        let valuesRef = [];

        Array.from(nodes).forEach( function(node) {
            let rid = node.getAttribute("rid");
            let refcell = node.getElementsByClassName(selid.split('-')[0])[0];
            nodesRef[rid] = node;
            if (selid === "date-order") {
                let date = new Date(refcell.innerText);
                valuesRef.push([date, rid]);
            } else if (selid === "state-order") {
                let stateVal = stateValues[node.getAttribute("state")];
                valuesRef.push([stateVal, rid]);
            } else {
                let text = refcell.innerText;
                valuesRef.push([text, rid]);
            }
        });
        return [nodesRef, valuesRef];
    }

    sort(order, valuesRef) {
        let sorted;
        if (order == "asc") {
            console.log("ascending ordering");
            sorted = valuesRef.sort(([a,b], [c,d]) => {
                if (a > c)
                    return 1;
                if (a < c)
                    return -1;
                return 0;
            });

        } else if (order == "des") {
            console.log("descending ordering");
            sorted = valuesRef.sort(([a,b], [c,d]) => {
                if (a > c)
                    return -1;
                if (a < c)
                    return 1;
                return 0;
            });
        }
        return sorted;
    }

    inject(valuesRef, nodesRef) {
        const table = document.getElementById("room-table");
        table.innerHTML = "";
        for (var [v, rid] of valuesRef) {
            let node = nodesRef[rid];
            table.appendChild(node);
        }
    }

    modifySortingStates(selid, next) {
        let selector = document.getElementById(selid);
        let others = document.getElementsByClassName("order");
        selector.innerHTML = next;
        Array.from(others).forEach( function(node) {
            if (node.id != selid) {
                node.innerHTML = "-";
            } 
        });
    }
}
