import base64
from fpdf import FPDF
from copy import deepcopy


class PDF(FPDF):
    """PDF BUILDER CLASS INHERITE FROM FPDF CLASS INSTANCE
    GENERATE PDF WITH QRCODE AND ROOM INFORMATIONS
    TRANSMIT PDF AS BASE64 STRING

    ATTR
    @width (int): width of a pdf page
    @height (int): height of a pdf page
    @font_size (int): font size of the pdf
    """

    width = 210
    height = 297
    font_size = 16

    def draw_qrcode_box(self, x: float, y: float, qrcode, caption):
        """draw container of size x*y
        contain QRCODE and supliers informations as caption"""
        self.rect(x, y, 170, 50, "")
        self.rect(x + 2, y + 2, 46, 46, "")
        self.image(qrcode, x + 5, y + 5, 40, 40, "PNG")
        self.rect(x + 60, y + 2, 100, 46, "")
        self.set_xy(x + 65, y + 5)
        self.cell(0, 7, f"**numéro de commande :** {str(caption['id'])}", markdown=True)
        self.set_xy(x + 65, y + 15)
        self.multi_cell(
            0,
            7,
            self.break_string(90, f"**fournisseur :** {caption['supplier']}"),
            markdown=True,
        )  #

    def break_string(self, w, str):
        """break caption string to fit long cation into container
        return breaked caption"""
        line_break = int(round(w / 3, 0)) - 1

        spliter = True
        breaked_str = ""
        copy = deepcopy(str)

        if len(str) > line_break:
            while spliter:
                space_idx = 0
                for i in range(len(copy)):
                    if copy[i] == " ":
                        space_idx = i

                    if i == len(copy) - 1:
                        breaked_str += copy
                        spliter = False
                        break

                    if i != 0 and i % line_break == 0 and space_idx != 0:
                        breaked_str += copy[:space_idx] + "\n"
                        copy = copy[space_idx:]
                        break

                    elif i != 0 and i % line_break == 0 and space_idx == 0:
                        breaked_str += copy[:line_break] + "\n"
                        copy = copy[line_break:]
                        break

            return breaked_str

        else:
            return str

    def generate_pdf(self, qrcode: list, caption: list):
        self.set_font("Helvetica", "", 16)
        self.add_page()

        space = self.height
        y_sep = 20
        place = 0
        n_page = 0
        for i in range(len(qrcode)):
            if (space - y_sep + 50) <= y_sep + 50:
                space = self.height
                place = 0
                n_page += 1
                self.add_page()

            if place == 0:
                self.draw_qrcode_box(20, y_sep, qrcode[i], caption[i])
                space -= y_sep + 50
                place += 1
            elif i > 0:
                self.draw_qrcode_box(
                    20, y_sep + place * 50 + place * y_sep, qrcode[i], caption[i]
                )
                space -= y_sep + 50
                place += 1

        return base64.b64encode(self.output()).decode("latin-1")
