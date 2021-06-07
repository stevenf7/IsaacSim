import carb, omni.ext, omni.kit.commands, omni.ui as ui, os, asyncio
from enum import Enum
from pxr import UsdGeom
import io
from PIL import Image, ImageChops
import numpy as np
import asyncio
import threading
import time
import signal

from omni.isaac.onshape.scripts.style import UI_STYLES
from omni.isaac.onshape.client import OnshapeClient
from omni.isaac.onshape.widgets.elements_widget import ElementGridView

supported_elements = ["Assembly"]  # , "Part", "Part Studio"]


class DocumentItem(ui.AbstractItem):
    def __init__(self, document_id):
        super().__init__()
        self.document_id = document_id
        self.document = None
        self.__thumb_img = None
        self.populate_document()
        self.populate_doc_type()
        self._byte_img_provider = ui.ByteImageProvider()
        self.__get_thumb()
        self.document_type = None
        self.elements = []
        self._children = []
        self._selected = False
        self._element_grid_view = None

    def populate_document(self):
        def get_doc():
            self.document = OnshapeClient.get().documents_api.get_document(self.document_id)

        self._doc_task = threading.Thread(target=get_doc)
        self._doc_task.start()

    def get_document(self):
        self._doc_task.join()
        return self.document

    def on_click(self):
        if self._widget:
            if self._element_grid_view:
                # print("selected")
                for card in self._element_grid_view._cards:
                    card.selected = False

    def populate_doc_type(self):
        def get_doc_type():
            self.elements = [
                i
                for i in OnshapeClient.get().documents_api.get_elements_in_document(
                    self.document_id, "w", self.get_workspace()
                )
                if i["type"] in supported_elements
            ]
            if len(self.elements) == 1:
                # if self.elements[0]["type"] == "Part Studio":
                #     self.parts = OnshapeClient.get().parts_api.get_parts_wmve(self.document_id,'w',self.get_workspace(), self.elements[0]['id'])
                #     if len(self.parts) == 1:
                #         self.document_type = "Part"
                #     else:
                #         self.document_type = "Part Studio"
                # else:
                self.document_type = self.elements[0]["type"]
            else:
                self.document_type = "Document"

        self._doc_type_task = threading.Thread(target=get_doc_type)
        self._doc_type_task.start()

    def get_document_type(self):
        self._doc_type_task.join()
        return self.document_type

    def get_elements(self):
        self._doc_type_task.join()
        return self.elements

    def get_workspace(self):
        return self.get_document()["default_workspace"]["id"]

    def get_name(self):
        return self.get_document()["name"]

    def get_thumb(self):
        # self.img_task.join()
        return self._byte_img_provider

    def get_thumb_img(self):
        return self.__thumb_img

    def __get_thumb(self):

        # Download largest available thumb size
        # r = OnshapeClient.get().thumbnails_api.get_document_thumbnail_with_size(self.document_id, self.get_workspace(), thumb_sizes["sizes"][-1]["size"], _preload_content=False)
        def trim(im):
            bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
            diff = ImageChops.difference(im, bg)
            diff = ImageChops.add(diff, diff, 2.0, -100)
            bbox = diff.getbbox()
            if bbox:
                return im.crop(bbox)
            return im

        def get_thumb():

            try:
                thumb_sizes = OnshapeClient.get().thumbnails_api.get_document_thumbnail(
                    self.document_id, self.get_workspace()
                )
                sizes = [
                    int("".join(filter(str.isdigit, thumb_sizes["sizes"][i]["size"])))
                    for i in range(len(thumb_sizes["sizes"]))
                ]
                idx = sorted(range(len(sizes)), key=lambda k: sizes[k])
                # print(idx)
                r = OnshapeClient.get().thumbnails_api.get_document_thumbnail_with_size(
                    self.document_id,
                    self.get_workspace(),
                    thumb_sizes["sizes"][idx[-1]]["size"],
                    _preload_content=False,
                )
                stream = io.BytesIO(r.data)
                pil_img = trim(Image.open(stream))
                size = pil_img.size
                scale = 100.0 / size[1]
                self.__thumb_img = np.array(
                    pil_img.resize((int(size[0] * scale), int(size[1] * scale)), resample=Image.LANCZOS)
                )
                # print(size,self.__thumb_img.shape)
                self._byte_img_provider.set_bytes_data(
                    self.__thumb_img.flatten().tolist(), [self.__thumb_img.shape[1], self.__thumb_img.shape[0]]
                )
            except:
                pass

        self.img_task = threading.Thread(target=get_thumb)
        self.img_task.start()
        # print(self._byte_img_provider)

    def toggle_elements_visible(self):
        if self._element_grid_view:
            self._element_grid_view.visible = not self._element_grid_view.visible
            self._element_frame.visible = self._element_grid_view.visible
            return self._element_grid_view.visible
        return False

    def clicked(self):
        pass
        # if self._element_grid_view:
        #     for card in self._element_grid_view._cards.values():
        #         card.selected = False

    def get_selected_element(self):
        if len(self.get_elements()) == 1:
            return self.get_elements()
        else:
            return self._element_grid_view.selections

    def build_element_grid_view(self, double_clicked_fn=None):
        self._element_frame = ui.VStack(
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            auto_resize=True,
            style={"background_color": 0x2223211F},
        )
        with self._element_frame:
            with ui.VStack():
                with ui.ZStack():
                    ui.Rectangle(style={"background_color": 0x88000000, "margin": 8, "border_radius": 10})
                    with ui.VStack():
                        ui.Spacer(height=10)
                        self._element_grid_view = ElementGridView(
                            "NvidiaDark", self, mouse_double_clicked_fn=double_clicked_fn
                        )
                        ui.Spacer(height=5)
                ui.Spacer(height=2)
        self._element_frame.visible = False
        self._element_grid_view.visible = False


class DocumentListModel(ui.AbstractItemModel):
    def __init__(self,):
        super().__init__()
        # self._children = []
        self.current_offset = 0
        self._step = 20
        self.query = ""
        self.filter = -1
        self.ownerType = 1
        self.owner_q = ""
        self.sortColumn = "createdAt"
        self.sortOrder = "desc"
        self.current_offset = 0
        self._children = []
        self.lock = threading.Semaphore(1)
        self.task = threading.Thread(target=self._list_all_docs)
        self._element_grid_view = None
        self.task.start()
        # self.list_all_docs()
        self.next = True
        # self._item_changed(None)

    def list_all_docs(self, query="", filter_type=-1, owner="", ownerType=1, sortColumn="createdAt", sortOrder="desc"):
        self.query = query + "*"
        self.filter = filter_type
        self.ownerType = ownerType
        self.sortColumn = sortColumn
        self.sortOrder = sortOrder
        self.current_offset = 0
        self.task = threading.Thread(target=self._list_all_docs)
        self.task.start()

    def _list_all_docs(self):
        # print(self.filter)
        query = self.query
        if (
            self.filter >= 0
        ):  # for some reason adding the filter option when none is selected makes it block to local docs only.
            r = OnshapeClient.get().documents_api.get_documents(
                limit=self._step,
                offset=0,
                q=self.query,
                filter=self.filter,
                owner_type=self.ownerType,
                sort_column=self.sortColumn,
                sort_order=self.sortOrder,
            )
        else:
            r = OnshapeClient.get().documents_api.get_documents(
                limit=self._step,
                offset=0,
                q=self.query,
                owner_type=self.ownerType,
                sort_column=self.sortColumn,
                sort_order=self.sortOrder,
            )
        with self.lock:
            # If query text didn't change since the documents were fetched, otherwise drop update as there's another one oncoming
            if query == self.query:
                if r.next:
                    self.current_offset = self._step
                    self.next = True
                else:
                    self.next = False
                self._children = [DocumentItem(doc["id"]) for doc in r["items"]]
                self._item_changed(None)

    def get_next_page(self):
        def get_next():
            with self.lock:
                if self.next:
                    if self.filter >= 0:
                        r = OnshapeClient.get().documents_api.get_documents(
                            limit=self._step,
                            offset=self.current_offset,
                            q=self.query,
                            filter=self.filter,
                            owner_type=self.ownerType,
                            sort_column=self.sortColumn,
                            sort_order=self.sortOrder,
                        )
                    else:
                        r = OnshapeClient.get().documents_api.get_documents(
                            limit=self._step,
                            offset=self.current_offset,
                            q=self.query,
                            owner_type=self.ownerType,
                            sort_column=self.sortColumn,
                            sort_order=self.sortOrder,
                        )

                    if r.next:
                        self.current_offset += self._step
                    else:
                        self.next = False
                    self._children = self._children + [DocumentItem(doc["id"]) for doc in r["items"]]
                    self._item_changed(None)

        task = threading.Thread(target=get_next)
        task.start()

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        """
        if item and isinstance(item, DocumentItem):
            if column_id == 1:
                return item.get_name()
            elif column_id == 0:
                return item.get_thumb()

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            return []
        else:
            return self._children


class DocumentListDelegate(ui.AbstractItemDelegate):
    def __init__(self, style):
        super().__init__()
        self.num_columns = 1
        self._style = style
        self._on_mouse_double_clicked = None

    def set_on_mouse_double_clicked(self, function):
        self._on_mouse_double_clicked = function

    def on_mouse_double_clicked(self, item):
        if self._on_mouse_double_clicked:
            self._on_mouse_double_clicked(item)

    def build_branch(self, model, item, column_id, level, expanded):
        pass

    def add_List_view(self, listView):
        self.listView = listView

    def build_widget(self, model, item, column_id, level, expanded):
        if item:
            with ui.VStack():
                with ui.HStack(
                    height=0,
                    width=ui.Percent(100),
                    style=self._style,
                    style_type_name_override="TreeView",
                    mouse_double_clicked_fn=(lambda x, y, b, _: self.on_mouse_double_clicked(item)),
                    mouse_pressed_fn=(lambda x, y, b, _, i=item: item.clicked()),
                    auto_resize=True,
                ):
                    with ui.ZStack(width=100):
                        ui.Rectangle(
                            height=100,
                            width=100,
                            style={
                                "margin": ui.Pixel(5),
                                "background_color": 0xFF444444,
                                "border_color": 0xFF222222,
                                "border_width": 0.5,
                                "border_radius": 10,
                            },
                        )
                        ui.ImageWithProvider(
                            item.get_thumb(), height=100, width=100, style={"border_radius": 10, "margin": 10}
                        )
                    with ui.VStack(style={"aligmnent": ui.Alignment.LEFT_TOP}):
                        ui.Spacer(height=6)
                        with ui.ZStack(height=ui.Pixel(0)):
                            ui.Rectangle(
                                height=20,
                                width=ui.Percent(100),
                                style={"background_color": 0xFF444444, "border_radius": 3},
                            )
                            with ui.HStack():
                                ui.Spacer(width=3)
                                ui.Label(
                                    item.get_name(),
                                    style={"aligmnent": ui.Alignment.LEFT_TOP, "margin": ui.Pixel(3)},
                                    height=ui.Pixel(0),
                                )
                        ui.Spacer(height=3)
                        with ui.HStack(height=0, style=self._style, style_type_name_override="TreeView"):
                            ui.Spacer(width=8)
                            ui.Label(
                                "Date created (modified):",
                                width=ui.Percent(0),
                                style_type_name_override="TreeView",
                                style=self._style,
                            )
                            ui.Spacer(width=3)
                            ui.Label(
                                item.get_document()["default_workspace"]["created_at"].strftime("%Y-%m-%d %H:%M"),
                                style={"color": 0xFF444444},
                                width=ui.Percent(0),
                            )
                            ui.Spacer(width=3)
                            ui.Label(
                                "({})".format(
                                    item.get_document()["default_workspace"]["modified_at"].strftime("%Y-%m-%d %H:%M")
                                ),
                                style={"color": 0xFF444444},
                                width=ui.Percent(0),
                            )
                        with ui.HStack(height=0, style={"margin": 0}):
                            ui.Spacer(width=8)
                            ui.Label("Author:", width=ui.Percent(0), style_type_name_override="TreeView")
                            ui.Spacer(width=3)
                            ui.Label(
                                item.get_document()["default_workspace"]["creator"]["name"], style={"color": 0xFF444444}
                            )
                        with ui.HStack(height=0, style={"margin": 0}):
                            ui.Spacer(width=8)
                            ui.Label("Owner:", width=ui.Percent(0), style_type_name_override="TreeView")
                            ui.Spacer(width=3)
                            ui.Label(item.get_document()["owner"]["name"], style={"color": 0xFF444444})

                        with ui.HStack(height=0, style={"margin": 0}):
                            ui.Spacer(width=8)
                            ui.Label("Type:", width=ui.Percent(0), style_type_name_override="TreeView")
                            ui.Spacer(width=3)
                            ui.Label(item.get_document_type(), style={"color": 0xFF444444}, width=0)
                        if len(item.elements) > 1:
                            with ui.ZStack(height=18):
                                with ui.VStack():
                                    ui.Spacer(height=3)
                                    ui.Rectangle(
                                        style={
                                            "margin_width": ui.Pixel(8),
                                            "background_color": 0x22FFFFFF,
                                            "border_radius": 3,
                                        }
                                    )
                                    ui.Spacer(height=3)
                                with ui.HStack(height=18):

                                    def toggle(button, button2, item):
                                        value = item.toggle_elements_visible()
                                        button.visible = not value
                                        button2.visible = value

                                    down = ui.Button(
                                        name="arrow_down", style=self._style, width=ui.Percent(100), height=18
                                    )
                                    up = ui.Button(
                                        name="arrow_up",
                                        style=self._style,
                                        visible=False,
                                        width=ui.Percent(100),
                                        height=18,
                                    )
                                    down.set_clicked_fn(lambda a=down, b=up, c=item: toggle(a, b, c))
                                    up.set_clicked_fn(lambda a=down, b=up, c=item: toggle(a, b, c))
                                    up.visible = False
                if len(item.elements) > 1:
                    item.build_element_grid_view(lambda x, y, b, item=item: self.on_mouse_double_clicked(item))
