
from Model import get_embedding
from docutils.utils import Reporter
from docutils.core import publish_file
from docutils.parsers.rst import roles, nodes
from bs4 import BeautifulSoup
import os
from upgraider.Database import Session, DeprecationComment, LibReleaseNote
import re
import json

def parse_html(html_file: str):
    deprecation_items = []

    with open(html_file, 'r') as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        for section in soup.find_all("div"):
            section_id = section.get('id')
            
            if section_id and ('deprecat' in section_id.lower() or 'api' in section_id.lower()):
                for list_item in section.find_all("li"):
                    deprecation_items.append(list_item.text)

                for paragraph in section.find_all("p"):
                    text = paragraph.text
                    
                    next_sibling = paragraph.find_next_sibling("pre")
                    if next_sibling is not None:
                        text += "\n" +  next_sibling.text 
                    
                    deprecation_items.append(text)

    
    return deprecation_items

def save_items(dep_items: list[str], session, release_id):
    for item in dep_items:
        embedding = json.dumps(get_embedding(item))
        session.add(DeprecationComment(
            content=item,
            lib_release_note=release_id,
            embedding=embedding
        ))
    
        session.commit()

def get_version_from_filename(filename: str):
    result = re.search(r"(?P<major> 0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)?(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?", filename)
    if result is not None:
        version = result.group('major') + "." + result.group('minor')

        if result.group('patch') is not None:
            version += "." + result.group('patch')
    
        return version
    
    return None

def main():
    script_dir = os.path.dirname(__file__)
    roles.register_generic_role('issue', nodes.emphasis)
    roles.register_generic_role('ref', nodes.emphasis)
    roles.register_generic_role('meth', nodes.emphasis)
    roles.register_generic_role('class', nodes.emphasis)
    roles.register_generic_role('func', nodes.emphasis)
    roles.register_generic_role('attr', nodes.emphasis)

    libraries_folder = os.path.join(script_dir, "../../libraries")
    for lib_dir in os.listdir(libraries_folder):
        if lib_dir.startswith("."):
            continue

        print(f"Populating DB with release note data for {lib_dir}...")

        session = Session()
  
        lib_path = os.path.join(script_dir, f"../../libraries/{lib_dir}")
        
        for note in os.listdir(os.path.join(lib_path, "releasenotes")):
            version = get_version_from_filename(note)
            print(f"Processing release note {note} for version {version}...")
            if note.startswith(".") or not note.endswith(".rst"):
                continue

            lib_release = session.query(LibReleaseNote).filter(LibReleaseNote.library == lib_dir).filter(LibReleaseNote.filename == note).first()

            if lib_release is not None:
                continue # Release note already exists in DB

            lib_release = LibReleaseNote(
                library=lib_dir,
                filename=note,
                version=version
            )

            session.add(lib_release)
            session.commit()

            release_id = lib_release.id

            base_name = os.path.splitext(note)[0]
            output_html_file = os.path.join(lib_path, "releasenotes", f"{base_name}.html")

            source_path = os.path.join(lib_path, "releasenotes", note)
            
            publish_file(source_path=source_path, writer_name='html', destination_path=output_html_file, settings_overrides={'report_level':Reporter.SEVERE_LEVEL})
            deprecated_items = parse_html(output_html_file)
            

            print(f"Found {len(deprecated_items)} deprecated items for {note}")
            save_items(deprecated_items, session=session, release_id=release_id)
            os.remove(output_html_file)
            print("Finished embedding and saving items")
        
        session.commit()
        session.close()


    
    

if __name__ == "__main__":
    main()