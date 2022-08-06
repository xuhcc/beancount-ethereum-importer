build:
	python -m build --sdist --wheel --outdir dist/

_deploy:
	twine upload dist/*

deploy: build _deploy

clean:
	rm -r build/ dist/
