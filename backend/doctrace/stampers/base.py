from abc import ABC, abstractmethod

class BaseStamper(ABC):
    @abstractmethod
    def stamp(self, input_pdf_path: str, output_pdf_path: str, bitstring: str) -> bool:
        """
        Stamps the bitstring into the PDF and writes the output to output_pdf_path.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def extract(self, pdf_path: str) -> str:
        """
        Extracts the bitstring from the PDF.
        Returns the extracted binary string.
        """
        pass
