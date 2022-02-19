from PIL import Image, ImageFilter
import shutil
import fitz
import os
import io
import time


# maximum 9999 pages
# just for only image pdf



DEFAULT_QUALITY = 6
DEFAULT_DPI = (300, 300)
DEFAULT_SIZE_RATIO = 100
DEFAULT_IMAGE_RADIUS = 2
DEFAULT_IMAGE_FILTER_SIZE = 3
DEFAULT_IMAGE_DIR = "image_page"



######################## Algorithm ########################

#------------------------------------------- Extract Image -------------------------------------------
# folder is input folder name.(just name)
def extractImg(pdf_filename, folder):
    try:
        shutil.rmtree(folder)
        os.mkdir(folder)
    except:
        os.mkdir(folder)
    
    pdf_file = fitz.open(pdf_filename)
    isJPG = True
    ones = 1
    tens = 0
    hundreds = 0
    thousands = 0

    for page_index in range(len(pdf_file)):
        page = pdf_file[page_index]
        try:
            for img in page.get_images():
                xref = img[0]
                base_image = pdf_file.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                if str(image_ext).lower() != 'jpg' or str(image_ext).lower() != 'jpeg':
                    isJPG = False
                image = Image.open(io.BytesIO(image_bytes))
                filename = str(thousands) + str(hundreds) + str(tens) + str(ones) +  "." + str(image_ext)
    
                image.save(open(folder + "\\" + filename, "wb"))
                ones += 1
                if ones > 9:
                    tens += 1
                    ones = 0
                if tens > 9:
                    hundreds += 1
                    tens = 0
                if hundreds > 9:
                    thousands += 1
                    hundreds = 0
        except:
            continue

    return isJPG


#------------------------------------------- Optimize Image -------------------------------------------
def OptimizeImg(InputImg, OutputImg, quality, dpi, img_size_ratio, radius, filter_size):
    img = Image.open(InputImg)
    w = int(img.size[0] * img_size_ratio / 100)
    h = int(img.size[1] * img_size_ratio / 100)
    img = img.resize((w, h), Image.ANTIALIAS)

    img_output = img.filter(ImageFilter.GaussianBlur(radius=radius))
    img_output = img_output.filter(ImageFilter.MinFilter(size=filter_size))
    img_output.save(OutputImg, optimize=True, quality=quality, dpi=dpi)


def OptimizeImg_Dir(InputImageDir, OutputImageDir, quality, dpi, img_size_ratio, radius, filter_size):
    imglst = os.listdir(InputImageDir)
    for image_name in imglst:
        OptimizeImg(InputImageDir + "\\" + image_name, 
                    OutputImageDir + "\\" + image_name,
                    quality, dpi, img_size_ratio, radius, filter_size)


#------------------------------------------- Convert to JPG -------------------------------------------
def Convert2JPG(InputImg, OutputImg):
    img = Image.open(InputImg)
    mode = img.mode
    if mode[len(mode) - 1] == 'A':
        img = img.convert(mode[:len(mode) - 1])
        img.save(InputImg)
    
    newImgPath = os.path.splitext(OutputImg)[0] + "-temp.jpeg"
    img.save(newImgPath, format="JPEG")

    os.remove(InputImg)
    os.rename(newImgPath, newImgPath.replace("-temp", ""))


def Convert2JPG_Dir(InputImageDir, OutputImageDir):
    imglst = os.listdir(InputImageDir)
    for image_name in imglst:
        Convert2JPG(InputImageDir + "\\" + image_name, OutputImageDir + "\\" + image_name)


#------------------------------------------- Replace Image -------------------------------------------
def updateImageFromDir(pdf_filename, new_filename, ImageDirectory):
    image_list = os.listdir(ImageDirectory)
    doc = fitz.Document(pdf_filename)

    for i in range(doc.page_count):
        page = doc.load_page(i)
        image_rectangle = page.rect

        page.clean_contents()
        xref = page.get_contents()[0]
        contlines = doc.xref_stream(xref).splitlines()
        for j in range(len(contlines)):
            line = contlines[j]
            if line.startswith(b"/Im") and line.endswith(b" Do"):
                contlines[j] = b""
        cont = b"\n".join(contlines)
        doc.update_stream(xref, cont)

        image_name = ImageDirectory + "\\" + image_list[i]
        page.insert_image(image_rectangle, filename = image_name)
        page.clean_contents()

    doc.save(new_filename, garbage=3, deflate=True)



#------------------------------------------- Compress -------------------------------------------
def compressPDF(inputPDF, outputPDF, quality, dpi, img_size_ratio, radius, filter_size, ImageDirectory=DEFAULT_IMAGE_DIR):
    print("\nFile:", os.path.basename(inputPDF))
    
    try:
        if os.path.exists(os.path.dirname(outputPDF)) == False:
            os.mkdir(os.path.dirname(outputPDF))
        start = time.time()
        img = extractImg(inputPDF, ImageDirectory)
        if img == False:
            Convert2JPG_Dir(ImageDirectory, ImageDirectory)
        OptimizeImg_Dir(ImageDirectory, ImageDirectory, quality, dpi, img_size_ratio, radius, filter_size)
        updateImageFromDir(inputPDF, outputPDF, ImageDirectory)
        end = time.time()

        # Info stat
        before = round(os.path.getsize(inputPDF)/(1024**2), 2)
        after = round(os.path.getsize(outputPDF)/(1024**2), 2)
        ratio = round(100 * (1 - after / before), 2)
        print(before,  "MB ---->", after, "MB")
        print("Ratio:", ratio, "%")
        print("Time:", round(end - start, 1))

        shutil.rmtree(ImageDirectory)
    except:
        print("Having some problem")


def compressPDF_Dir(inputDir, outputDir, quality, dpi, img_size_ratio, radius, filter_size, ImageDirectory=DEFAULT_IMAGE_DIR):
    if os.path.exists(outputDir) == False:
        os.mkdir(outputDir)
    file = os.listdir(inputDir)
    for f in file:
        inputPDF = inputDir + "\\" + f
        if (os.path.splitext(inputPDF)[1] == ".pdf"):
            outputPDF = outputDir + "\\" + f
            compressPDF(inputPDF, outputPDF, quality, dpi, img_size_ratio, radius, filter_size, ImageDirectory)
        else:
            continue



#------------------------------------------- Read information from txt file -------------------------------------------
######################## Choice ########################
# 1: compress file
# 2: compress dir
def readFile(filename):
    elements = open(filename, "r", encoding="utf-8").read().strip().split("\n\n")
    lst = []
    for e in elements:
        dic = {
                "choice": 1, "input": None, "output": None, "quality": DEFAULT_QUALITY,
                "dpi": DEFAULT_DPI, "image_size": DEFAULT_SIZE_RATIO, 
                "radius": DEFAULT_IMAGE_RADIUS, "filter_size": DEFAULT_IMAGE_FILTER_SIZE
              }

        lines = e.split("\n")
        start = 2
        dic["input"] = lines[0]

        if os.path.isdir(dic["input"]):
            dic["choice"] = 2

        # Find output path
        if dic["choice"] == 1:
            output = os.path.dirname(dic["input"]) + "\\compressed"
        if dic["choice"] == 2:
            output = dic["input"] + "\\compressed"
        if len(lines) > 1: # May have output path
            if os.path.isdir(lines[1]) == False:
                dic["output"] = output
                start = 1
            else:
                dic["output"] = lines[1]
        else: # Just have input path, no more info
            dic["output"] = output
            start = 1

        for i in range(start, len(lines)):
            parameter = lines[i].strip().split('\t')
            if parameter[0].lower() == "dpi":
                dic[parameter[0].lower()] = eval(parameter[1])
            else:
                dic[parameter[0].lower()] = int(parameter[1])

        lst.append(dic)

    return lst


def Main(filename):
    elements = readFile(filename)
    for dic in elements:
        if dic["choice"] == 1:
            outputPDF = dic["output"] + "\\" + os.path.basename(dic["input"])
            compressPDF(dic["input"], outputPDF, dic["quality"], dic["dpi"], 
                        dic["image_size"], dic['radius'], dic["filter_size"])
        if dic["choice"] == 2:
            compressPDF_Dir(dic["input"], dic["output"], dic["quality"], dic["dpi"], 
                            dic["image_size"], dic['radius'], dic["filter_size"])





if __name__ == '__main__':
    filename = input("Enter txt file name (Enter '0' to exit): ")
    
    if filename != '0':
        start = time.time()
        Main(filename)
        end = time.time()

        try:
            shutil.rmtree(DEFAULT_IMAGE_DIR)
        except:
            ""

        print("\nDone!!")
        print("Time: ", (end - start))
        
