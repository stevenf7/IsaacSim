import os

import requests
import validators

mypath = "docs"
myList = []
myList.extend(
    "Page Count, "
    + "File, "
    + "Location (repo), "
    + "Web URL, "
    + "Val Code, "
    + "Validation Summary, "
    + "File Size"
    + "\r"
)

rstCounter = 0
rstCountTotal = 0
myPrefix = "omnidocs: "
outputFileName = "output_report" + ".txt"
myStatus = ""
fileSize = 0

print("Working Directory: " + os.getcwd())

for root, dirs, files in os.walk(mypath):
    for file in files:
        if file.endswith(".rst"):
            rstCountTotal += 1


for root, dirs, files in os.walk(mypath):
    for file in files:
        if file.endswith(".rst"):
            rstCounter += 1
            path = myPrefix + os.path.join(root, file)
            file_stats = os.stat(os.path.join(root, file))
            fileSize = file_stats.st_size

            path = path.replace("\\", "/")
            webPath = path.replace(myPrefix + "docs/", "https://docs.omniverse.nvidia.com/")
            webPath = webPath.replace(".rst", ".html")
            # replace the portal with web prefix
            webPath = webPath.replace("/app_audio2face/", "/audio2face/latest/")
            webPath = webPath.replace("/app_code/", "/code/latest/")
            webPath = webPath.replace("/app_composer/", "/composer/latest/")
            webPath = webPath.replace("/app_create/", "/create/latest/")
            webPath = webPath.replace("/explorer/", "/explore/latest/")
            webPath = webPath.replace("/app_farm/", "/farm/latest/")
            webPath = webPath.replace("/app_isaacsim/", "/isaacsim/latest/")
            webPath = webPath.replace("/app_kaolin/", "/kaolin/latest/")
            webPath = webPath.replace("/app_machinima/", "/machinima/latest/")
            webPath = webPath.replace("/app_navigator/", "/navigator/latest/")
            webPath = webPath.replace("/app_omniverse-xr/", "/omniverse-xr/latest/")
            webPath = webPath.replace("/presener/", "/presenter/latest/")
            webPath = webPath.replace("/app_scene-optimizer/", "/scene-optimizer/latest/")
            webPath = webPath.replace("/app_showroom/", "/showroom/latest/")
            webPath = webPath.replace("/app_usdview/", "/usdview/latest/")
            webPath = webPath.replace("/app_view/", "/view/latest/")
            webPath = webPath.replace("/app_view_deprecated/", "/view_deprecated/latest/")
            webPath = webPath.replace("/common/", "/common/latest/")
            webPath = webPath.replace("/con_connect/", "/connect/latest/")
            webPath = webPath.replace("/content/", "/content/latest/")
            webPath = webPath.replace("/plat_omniverse/", "/platform/latest/")
            webPath = webPath.replace("/prod_content/", "/content/latest/")
            webPath = webPath.replace("/prod_data-aggregation-guide/", "/dang/latest/")
            webPath = webPath.replace("/prod_deployment/", "/deployment/latest/")
            webPath = webPath.replace("/prod_digital-twins/", "/digital-twins/latest/")
            webPath = webPath.replace("/prod_enterprise/", "/enterprise/latest/")
            webPath = webPath.replace("/prod_extensions/", "/extensions/latest/")
            webPath = webPath.replace("/prod_install-guide/", "/install-guide/latest/")
            webPath = webPath.replace("/prod_kit/", "/dev-guide/latest/")
            webPath = webPath.replace("/prod_launcher/", "/launcher/latest/")
            webPath = webPath.replace("/prod_materials-and-rendering/", "/materials-and-rendering/latest/")
            webPath = webPath.replace("/prod_nucleus/", "/nucleus/latest/")
            webPath = webPath.replace("/prod_services/", "/services/latest/")
            webPath = webPath.replace("/prod_simready/", "/simready/latest/")
            webPath = webPath.replace("/prod_usd/", "/usd/latest/")
            webPath = webPath.replace("/prod_usd_old/", "/usd_old/latest/")
            webPath = webPath.replace("/prod_utilities/", "/utilities/latest/")
            webPath = webPath.replace("/prod_workflows/", "/workflows/latest/")

            try:
                page = requests.get(webPath)
                # print(page.status_code)
                myStatus = str(page.status_code)

                if page.status_code == 404:
                    myValidation = "Validation Failed"
                else:
                    myValidation = "Validation Passed"

                print("Testing " + str(rstCounter) + " of " + str(rstCountTotal) + ": " + myValidation)

            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):

                webPath = "Error"

            myList.extend(
                str(rstCounter)
                + ", "
                + file
                + ", "
                + path
                + ", "
                + webPath
                + ", "
                + myStatus
                + ", "
                + myValidation
                + ", "
                + str(fileSize)
                + "\r"
            )

file = open(outputFileName, "w")

for line in myList:
    file.write(line)

file.close()
