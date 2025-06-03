这是一个按task list运行，去扫描task list中的项目对应的项目文件夹，根据扫描解决改写项目文件夹下的checklist.docx。
1. 运行前，请先填写工作目录下的task list，它是一个excel文件，内有一个项目列表，含项目号和项目创建人和项目负责人等信息。
2. 根据config.json中的task list map读取task list，获取项目信息
4. 遍历获取的项目信息,进行下列操作，
    1. 根据该项目的项目号（job_no），在shortcuts_path中获取项目对应的项目文件夹路径
    2. 扫描项目对应的项目文件夹，获取子文件夹的文件情况
    3. 根据获取的子文件夹的文件情况，填写checklist.docx的行5-18的列3的activeX控件
    4. 根据项目创建人和项目负责人，从sign_pics路径下获取对应的签名图片，插入到checklist.docx的表格行3列4单元格中
    5. 保存checklist.docx
